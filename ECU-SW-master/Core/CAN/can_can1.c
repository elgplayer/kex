// Created by Oscar Eriksson in June 2022
#include "stdint.h"
#include "string.h"
#include "can_can1.h"
 
__weak void can1_mcu_set_ecu_indicator_points_receive_callback(can1_mcu_set_ecu_indicator_points_t* can1_mcu_set_ecu_indicator_points){
   return; 
}
 
 
__weak void can1_dbu_status_1_transmit_callback(can1_dbu_status_1_t* can1_dbu_status_1){
   return; 
}
 
__weak void can1_ecu_status_transmit_callback(can1_ecu_status_t* can1_ecu_status){
   return; 
}

__weak void can1_potentiometer_status_transmit_callback(can1_potentiometer_status_t *can1_potentiometer_status)
{
   return;
}

uint8_t can1_mcu_set_ecu_indicator_points_decode(can1_mcu_set_ecu_indicator_points_t* can1_mcu_set_ecu_indicator_points, uint8_t data[8]){
    int8_t brake_light = 0;
    brake_light |= ((uint8_t)(data[0] & 0x01));
    can1_mcu_set_ecu_indicator_points->brake_light = (1.0 * (double)brake_light) + 0.0;

    int8_t r2d_sound = 0;
    r2d_sound |= ((uint8_t)(data[0] & 0x02) >> (uint8_t)1);
    can1_mcu_set_ecu_indicator_points->r2d_sound = (1.0 * (double)r2d_sound) + 0.0;

    int8_t assi_yellow_right = 0;
    assi_yellow_right |= ((uint8_t)(data[0] & 0x04) >> (uint8_t)2);
    can1_mcu_set_ecu_indicator_points->assi_yellow_right = (1.0 * (double)assi_yellow_right) + 0.0;

    int8_t assi_yellow_left = 0;
    assi_yellow_left |= ((uint8_t)(data[0] & 0x08) >> (uint8_t)3);
    can1_mcu_set_ecu_indicator_points->assi_yellow_left = (1.0 * (double)assi_yellow_left) + 0.0;

    int8_t assi_yellow_rear = 0;
    assi_yellow_rear |= ((uint8_t)(data[0] & 0x10) >> (uint8_t)4);
    can1_mcu_set_ecu_indicator_points->assi_yellow_rear = (1.0 * (double)assi_yellow_rear) + 0.0;

    int8_t assi_blue_right = 0;
    assi_blue_right |= ((uint8_t)(data[0] & 0x20) >> (uint8_t)5);
    can1_mcu_set_ecu_indicator_points->assi_blue_right = (1.0 * (double)assi_blue_right) + 0.0;

    int8_t assi_blue_left = 0;
    assi_blue_left |= ((uint8_t)(data[0] & 0x40) >> (uint8_t)6);
    can1_mcu_set_ecu_indicator_points->assi_blue_left = (1.0 * (double)assi_blue_left) + 0.0;

    int8_t assi_blue_rear = 0;
    assi_blue_rear |= ((uint8_t)(data[0] & 0x80) >> (uint8_t)7);
    can1_mcu_set_ecu_indicator_points->assi_blue_rear = (1.0 * (double)assi_blue_rear) + 0.0;

    return 1;
}

uint8_t can1_potentiometer_status_encode(can1_potentiometer_status_t *can1_potentiometer_status, uint8_t data[8])
{
    memset(data, 0, 8);

    // Add scaling or fancy stuff here.
    int16_t potentiometer_voltage = 1 * ((double)can1_potentiometer_status->potentiometer_voltage);
    data[0] |= (uint8_t)((uint16_t)can1_potentiometer_status << (uint16_t)4) & 0xf0;
    data[1] |= (uint8_t)((uint16_t)can1_potentiometer_status >> (uint16_t)4) & 0xff;

    return 1;
}

uint8_t can1_ecu_status_encode(can1_ecu_status_t* can1_ecu_status, uint8_t data[8]) {
    memset(data, 0, 8);
    int8_t rst_button = 1.0 * ((double)can1_ecu_status->rst_button - 0.0);
    data[0] |= (uint8_t)rst_button & 0xff;

    int8_t close_airs = 1.0 * ((double)can1_ecu_status->close_airs - 0.0);
    data[1] |= (uint8_t)close_airs & 0xff;

    int8_t ts_off = 1.0 * ((double)can1_ecu_status->ts_off - 0.0);
    data[2] |= (uint8_t)ts_off & 0xff;

    return 1;
}


 