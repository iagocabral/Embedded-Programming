#ifndef MQTT_H
#define MQTT_H

#include "mqtt_client.h"

extern esp_mqtt_client_handle_t client1;
extern esp_mqtt_client_handle_t client2;

void mqtt_start();
void mqtt_stop();

void mqtt_envia_mensagem(esp_mqtt_client_handle_t client, char * topico, char * mensagem);
void log_enviada_public(const char *topico, const char *mensagem);

#endif