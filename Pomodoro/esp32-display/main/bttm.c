#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"

#define BUTTON_PIN GPIO_NUM_15 // Pino onde o botão está conectado

static bool state_button = false;

void button_task(void *params)
{
    gpio_set_direction(BUTTON_PIN, GPIO_MODE_INPUT);
    gpio_set_pull_mode(BUTTON_PIN, GPIO_PULLUP_ONLY);

    while (true)
    {
        int button_state = gpio_get_level(BUTTON_PIN);
        
        if (button_state == 0) 
        {
            vTaskDelay(pdMS_TO_TICKS(50)); // Anti-bounce
            if (gpio_get_level(BUTTON_PIN) == 0)
            {
                state_button = !state_button; 
                printf("Estado do botão alterado para: %d\n", state_button);

                while (gpio_get_level(BUTTON_PIN) == 0) 
                { 
                    vTaskDelay(pdMS_TO_TICKS(50)); 
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}


bool get_button_state()
{
    return state_button;
}
