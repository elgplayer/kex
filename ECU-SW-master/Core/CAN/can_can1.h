// Created by Oscar Eriksson in June 2022
#ifndef _CAN_CAN1_
#define _CAN_CAN1_
 
#include "stdint.h"
#include "kthfspe_can.h"
 
 
typedef struct {
    int8_t activate_ts_button;
    int8_t ready_to_drive_button;
    float dbu_temperature;
} can1_dbu_status_1_t;
 
typedef struct {
    int8_t rst_button;
    int8_t close_airs;
    int8_t ts_off;
} can1_ecu_status_t;
 
typedef struct {
    int8_t brake_light;
    int8_t r2d_sound;
    int8_t assi_yellow_right;
    int8_t assi_yellow_left;
    int8_t assi_yellow_rear;
    int8_t assi_blue_right;
    int8_t assi_blue_left;
    int8_t assi_blue_rear;
} can1_mcu_set_ecu_indicator_points_t;

typedef struct
{
    float potentiometer_voltage;
} can1_potentiometer_status_t;


// Recieve callback
void can1_mcu_set_ecu_indicator_points_receive_callback(can1_mcu_set_ecu_indicator_points_t* can1_mcu_set_ecu_indicator_points);
 
void can1_dbu_status_1_transmit_callback(can1_dbu_status_1_t* can1_dbu_status_1);
 
void can1_ecu_status_transmit_callback(can1_ecu_status_t* can1_ecu_status);

void can1_potentiometer_status_transmit_callback(can1_potentiometer_status_t *can1_potentiometer_status);

// Transmit
void can1_dbu_status_1_transmit();
 
void can1_ecu_status_transmit();

void can1_potentiometer_status_transmit();


 
 
uint8_t can1_mcu_set_ecu_indicator_points_decode(can1_mcu_set_ecu_indicator_points_t* can1_mcu_set_ecu_indicator_points, uint8_t data[8]);
 
uint8_t can1_dbu_status_1_encode(can1_dbu_status_1_t* can1_dbu_status_1, uint8_t data[8]);
 
uint8_t can1_ecu_status_encode(can1_ecu_status_t* can1_ecu_status, uint8_t data[8]);

uint8_t can1_potentiometer_status_encode(can1_potentiometer_status_t *can1_potentiometer_status, uint8_t data[8]);

#endif