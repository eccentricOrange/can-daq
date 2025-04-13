idf_component_register(
    SRCS            "can-daq-idf.c"
    INCLUDE_DIRS    "."
    REQUIRES
        driver
        esp_timer
)