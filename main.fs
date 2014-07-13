#nowarn "21"  // Warning that the compiler can't check the recursive mailbox processor object
#nowarn "40"  // Also warning that the compiler can't check the recursive mailbox processor object

open SimplexNoise 

let (@@) fn x = fn x

let debugAgent = MailboxProcessor.Start(fun inbox ->
    let rec messageLoop =
        async {
            let! msg = inbox.Receive()
            printfn "%s" msg
            return! messageLoop
        }

    messageLoop
)

[<AutoOpen>]
module DomainTypes =
    type Terrain =
        | DeepWater
        | ShallowWater

        | SubtropicalDesert
        | Grassland
        | TropicalSeasonalForest
        | TropicalRainforest
        | TemperateDesert
        | TemperateDeciduousForest
        | TemperateRainforest
        | Shrubland
        | Taiga
        | Scorched
        | Bare
        | Tundra
        | Snow

    type Map = Terrain list list

    // Entities
    type ID = | ID of string
    type OwnerID = | OwnerID of string

    type Dot = {id:ID; owner:OwnerID; pos:(float * float); speed:float}
    type SomethingElse = {id:ID; owner:OwnerID; pos:(float * float); speed:float}

    type Entity =
        | EntityDot of Dot
        | EntitySomethingElse of SomethingElse

    type Color =
        | Red
        | Blue

    type Agent = {id:OwnerID; color:Color}

    type World = {ticks:int; agents:Agent list; map:Map; entities:Entity list;}

module Simplex =
    let makeNoise octaves persistance scale x y z =
        let total = 0.
        let frequency = scale
        let amplitude = 1.
        let maxAmplitude = 0.

        let rec getVal total octaves frequency amplitude maxAmplitude = 
            let noiseVal = SimplexNoise.Noise.Generate (float x*frequency, float y*frequency, float z*frequency)
            let amplifiedNoise = noiseVal * amplitude
            let total' = total + amplifiedNoise
            (*
            printfn "noiseVal: %A" noiseVal
            printfn "amplifiedNoise: %A" total
            printfn "maxAmplitude: %A" maxAmplitude
            *)
            match octaves with
            | 1 -> total / maxAmplitude
            | _ -> 
                let octaves' = octaves - 1
                let frequency' = frequency * 2.
                let maxAmplitude' = maxAmplitude + amplitude
                let amplitude' = amplitude * persistance
                getVal total' octaves' frequency' amplitude' maxAmplitude'
        getVal total octaves frequency amplitude maxAmplitude

    let makeMapNoise simplexFn smoothness max_x max_y =
        let getNoise x y z =
           simplexFn (float x*smoothness) (float y*smoothness) (float z*smoothness)

        [0..max_x]
            |> Array.ofList
            |> Array.Parallel.map (fun x ->
                [0..max_y]
                    |> Array.ofList
                    |> Array.Parallel.map (fun y -> getNoise x y 0.)
                    |> List.ofArray
            )
            |> List.ofArray

module Worldmaker =
    let max_x = 1000
    let max_y = 600

    /// <summary>Takes upper/lower value boundaries and bucket proportions and
    /// returns ranges of values each bucket can contain</summary>
    let makeBuckets lowerBound upperBound buckets =
        // Critical Chickens
        match (lowerBound, upperBound) with
        | (lowerBound, upperBound) when upperBound < lowerBound -> failwith @@ "Upper bound must be greater than lower bound"
        | _ -> ()

        let bucketSize = (upperBound - lowerBound) / (List.sum buckets)
        // Calculate the ceiling values for all buckets
        List.fold(fun acc elem ->  // Create list with minimum value for each bucket
            let elemSize = elem * bucketSize
            match acc with
            | x :: _ -> [x + elemSize] @ acc
            | [] -> [lowerBound + elemSize]  // Smallest bucket must have a ceiling equal to the smallest bucket
        ) [] buckets
            |> (fun l -> [upperBound] @ (List.tail l))  // Replace upper ceiling with upper bound
            |> List.rev

    /// <summary>Takes bucket ceilings and a value and returns the bucket the
    /// value falls into</summary>
    let bucketize buckets v =
        //debugAgent.Post @@ sprintf "buckets: %A,\t bucketCeils: %A,\tv: %A,\tbucketSize: %A" buckets bucketCeils v bucketSize
        buckets
            |> List.findIndex (fun bucketCeil -> v <= bucketCeil)  // Find buckets where our value is greater than the bottom of the bucket

    let private assignWater waterBuckets simplexFn x y =
        // Map our X and Y to different values, so we don't
        // get the same value as the existing cell
        let x' = ((float x ** 2.) / 180.) * 0.01
        let y' = ((float y ** 2.) / 180.) * 0.01
        let z = 0.
        simplexFn x' y' z
            |> bucketize waterBuckets
            |> (fun seg ->
                match seg with
                | 0 -> Some DeepWater
                | 1 -> Some ShallowWater
                | 2 -> None
                | _ -> failwith @@ sprintf "Invalid bucket: %i" seg
            )

    let private assignLand elevationBuckets moistureBuckets simplexValue =
        let elevation = bucketize elevationBuckets simplexValue
        let moisture = bucketize moistureBuckets simplexValue

        match (elevation, moisture) with
        | (0, 0) -> SubtropicalDesert
        | (0, 1) -> Grassland
        | (0, 2) | (0, 3) -> TropicalSeasonalForest
        | (0, 4) | (0, 5) -> TropicalRainforest

        | (1, 0) -> TemperateDesert
        | (1, 1) | (1, 2) -> Grassland
        | (1, 3) | (1, 4) -> TemperateDeciduousForest
        | (1, 5) -> TemperateRainforest

        | (2, 0) | (2, 1) -> TemperateDesert
        | (2, 2) | (2, 3) -> Shrubland
        | (2, 4) | (2, 5) -> Taiga
        | (3, 0) -> Scorched
        | (3, 1) -> Bare
        | (3, 2) -> Tundra
        | (3, 3) | (3, 4) | (3, 5) -> Snow

        | _ -> failwith "Invalid elevation/moisture combination"

    /// <summary>Accepts a 2D map and assigns each cell a terrain type</summary>
    let assignTerrain simplexFn map =
        let makeBuckets' = makeBuckets -1. 1.

        let waterBuckets = makeBuckets' [20.; 5.; 25.]
        let elevationBuckets = makeBuckets' [15.; 8.; 10.; 8.]
        let moistureBuckets = makeBuckets' [15.; 20.; 8.; 10.; 20.; 10.]

        map
            |> Array.ofList
            |> Array.Parallel.mapi (fun x row ->
                row
                    |> Array.ofList
                    |> Array.Parallel.mapi (fun y cellValue ->
                        // Decide whether this should be water or land
                        let shouldBeWater = assignWater waterBuckets simplexFn x y
                        match shouldBeWater with
                        | Some terrain -> terrain
                        | None -> assignLand elevationBuckets moistureBuckets cellValue  // Decide what kind of land this should be
                    )
                    |> List.ofArray
            )
            |> List.ofArray

module Utils =
    let FPS = 10

    let frames_to_secs (frames:int) = (double frames) / (double FPS)
    let secs_to_frames secs = secs * FPS
    let secs_to_ms secs = int @@ secs * 1000.

    let makeUUID () =
        let guid = System.Guid.NewGuid()
        guid.ToString()

    let updateListAt index newVal list_ =
        list_
            |> List.mapi (fun i el ->
                match i with
                | index -> newVal
                | _ -> el
            )

    let makeWorldUpdate f =
        [Some f]

module Agents =
    let makeOwnerID () =
        OwnerID @@ Utils.makeUUID ()

    let isMine agent elem =
        match elem with
        | EntityDot d -> d.owner = agent.id
        | EntitySomethingElse s -> s.owner = agent.id

    let hasEntities agent world =
        List.exists (isMine agent) world.entities

    let makeDecision world agent =
        match hasEntities agent world with
        | false ->
            Utils.makeWorldUpdate (fun newWorld ->
                printfn "Creating new entity"
                {
                    newWorld with
                        entities =
                            newWorld.entities @ [
                                EntityDot {
                                    Dot.id=ID (Utils.makeUUID ());
                                    owner=agent.id;
                                    pos=(0.,0.); speed=1.
                                }
                            ]
                }
            )
        | true -> [None]

module Engine =
    let initAgents () =
        [
            {Agent.id=Agents.makeOwnerID (); color=Color.Red}
        ]

    let makeGame () =
        let octaves = 9  // Higher than 10 makes no difference
        let persistance = 0.5
        let scale = 2.
        let smoothness = 0.004
        debugAgent.Post @@ "Making map"
        let simplexFn = Simplex.makeNoise octaves persistance scale
        let map =
            Simplex.makeMapNoise simplexFn smoothness 1100 600
            |> Worldmaker.assignTerrain simplexFn
        debugAgent.Post @@ "Map made"

        let agents = initAgents ()
        let world = {ticks=0; agents=agents; map=map; entities=[]}
        world

    let rec run world =
        printfn "%A" world.ticks
        let updates = Agents.makeDecision world world.agents.[0]
        let world' =
            updates
                |> List.fold (fun world update ->
                    match update with
                    | Some update -> update world
                    | None -> world
                ) world

        System.Threading.Thread.Sleep(Utils.secs_to_ms @@ Utils.frames_to_secs 1)
        run {world' with ticks = world.ticks + 1}


Engine.makeGame ()
    |> Engine.run
