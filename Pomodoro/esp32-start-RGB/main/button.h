#ifndef BUTTON_H
#define BUTTON_H

#include "driver/gpio.h"

#define BUTTON_GPIO             GPIO_NUM_0
#define POMODORO_TIME_MS        (2 * 1000)
#define BREAK_TIME_MS           (1 * 1000)
#define NUM_CYCLES              2

extern int button_state;
void button_init(void);
void pomodoro_task(void *pvParameter);
void send_button_state(int state);
void send_led_color(int color);

#endif