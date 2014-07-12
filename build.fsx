//include Fake lib
#r @"tools/FAKE.3.1.2/tools/FakeLib.dll"
open Fake
open Fake.FscHelper

let buildDir = "./build"

Target "Clean" (fun _ ->
    CleanDir buildDir
)

// Default target
Target "Default" (fun _ ->
    //trace "Hello World from FAKE"  // How to print debug output
    ["main.fs"]
    |> Fsc (fun parameters ->
        {parameters with References = ["packages/simplexnoise_1_01/SimplexNoise/bin/Debug/SimplexNoise.dll"]}
    )
)

Target "BuildApp" (fun _ ->
    ()
)

Target "MakeDeps" (fun _ ->
    !! "src/app/**/*.csproj"
        |> MSBuildRelease buildDir "Build"
        |> Log "AppBuild-Output: "
)

// Dependencies

"Default"
    ==> "MakeDeps"

"Clean"
    ==> "BuildApp"
    ==> "Default"

// start build
RunTargetOrDefault "Default"
