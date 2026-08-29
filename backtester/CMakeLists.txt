add_executable(
        stage1_replay
        src/main.cpp
)

target_compile_features(
        stage1_replay
        PRIVATE
        cxx_std_20
)

target_compile_options(
        stage1_replay
        PRIVATE
        -Wall
        -Wextra
        -Wpedantic
)