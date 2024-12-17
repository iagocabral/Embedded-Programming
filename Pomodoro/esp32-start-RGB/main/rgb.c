#include "rgb.h"
#include "driver/ledc.h"

#define LEDC_TIMER              LEDC_TIMER_0
#define LEDC_MODE               LEDC_LOW_SPEED_MODE
#define LEDC_OUTPUT_RED         (15)
#define LEDC_OUTPUT_GREEN       (5)
#define LEDC_OUTPUT_BLUE        (4)
#define LEDC_CHANNEL_RED        LEDC_CHANNEL_0
#define LEDC_CHANNEL_GREEN      LEDC_CHANNEL_1
#define LEDC_CHANNEL_BLUE       LEDC_CHANNEL_2
#define LEDC_DUTY_RES           LEDC_TIMER_8_BIT
#define LEDC_DUTY               (255)
#define LEDC_FREQUENCY          (5000)

void configure_rgb_channels(void) {
    // Configura o timer do LEDC
    ledc_timer_config_t ledc_timer = {
        .speed_mode       = LEDC_MODE,
        .timer_num        = LEDC_TIMER,
        .duty_resolution  = LEDC_DUTY_RES,
        .freq_hz          = LEDC_FREQUENCY,
        .clk_cfg          = LEDC_AUTO_CLK,
    };
    ledc_timer_config(&ledc_timer);

    // Configura os canais do LEDC
    ledc_channel_config_t ledc_channel[3] = {
        {
            .speed_mode     = LEDC_MODE,
            .channel        = LEDC_CHANNEL_RED,
            .timer_sel      = LEDC_TIMER,
            .intr_type      = LEDC_INTR_DISABLE,
            .gpio_num       = LEDC_OUTPUT_RED,
            .duty           = 0,
            .hpoint         = 0,
        },
        {
            .speed_mode     = LEDC_MODE,
            .channel        = LEDC_CHANNEL_GREEN,
            .timer_sel      = LEDC_TIMER,
            .intr_type      = LEDC_INTR_DISABLE,
            .gpio_num       = LEDC_OUTPUT_GREEN,
            .duty           = 0,
            .hpoint         = 0,
        },
        {
            .speed_mode     = LEDC_MODE,
            .channel        = LEDC_CHANNEL_BLUE,
            .timer_sel      = LEDC_TIMER,
            .intr_type      = LEDC_INTR_DISABLE,
            .gpio_num       = LEDC_OUTPUT_BLUE,
            .duty           = 0,
            .hpoint         = 0,
        }
    };

    for (int ch = 0; ch < 3; ch++) {
        ledc_channel_config(&ledc_channel[ch]);
    }
}

void set_rgb_color(uint8_t red, uint8_t green, uint8_t blue) {
    ledc_set_duty(LEDC_MODE, LEDC_CHANNEL_RED, red);
    ledc_update_duty(LEDC_MODE, LEDC_CHANNEL_RED);

    ledc_set_duty(LEDC_MODE, LEDC_CHANNEL_GREEN, green);
    ledc_update_duty(LEDC_MODE, LEDC_CHANNEL_GREEN);

    ledc_set_duty(LEDC_MODE, LEDC_CHANNEL_BLUE, blue);
    ledc_update_duty(LEDC_MODE, LEDC_CHANNEL_BLUE);
}