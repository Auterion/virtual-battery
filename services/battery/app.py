#!/usr/bin/env python3

import logging
import time
import datetime
import libmav


class VirtualBattery:
    voltage_battery_v = 12.0 
    current_battery_a = 0.0   
    energy_consumed_mAh = 0.0 
    battery_remaining = 50.0
    message_set = None
    battery_capacity_mAh = 100
    battery_health_percentage = 100
    load_current_a = 0.0
    low_battery_threshold = 0.0
    critical_battery_threshold = 0.0
    emergency_battery_threshold = 0.0
    average_current = 0.0
    num_battery_cells = 0.0
    voltage_divider = 0.0
    voltage_empty = 0.0
    internal_resistance = 0.0
    current_channel = 0.0
    battery_source = 0.0
    voltage_channel = 0.0
    voltage_charged = 0.0
    voltage_load_drop = 0.0
    voltage_load_ref = 0.0
    
    connection = None
    

    def __init__(self, message_set):
        self.message_set = message_set
        
        
    def update_state(self):

        self.load_current_a = 0.0  # Example load current
        discharge_rate = self.load_current_a / self.battery_capacity_mAh
        self.energy_consumed_mAh += discharge_rate

        # Update battery health (SoH)
        self.battery_health_percentage -= 0.001  # Example degradation rate

        # Update battery remaining percentage based on SoH and discharge
        self.battery_remaining = max(0, self.battery_remaining - discharge_rate / self.battery_health_percentage)

        # Simulate temperature effects on battery performance
        self.battery_temperature_c = self.calculate_temperature()

        # Update voltage based on remaining capacity and health
        self.voltage_battery_v = 12.0
        
    def calculate_temperature(self):
        return 25.0      
        
    def handle_param_value_message(self, msg):
        if msg.name == 'PARAM_VALUE':
            param_id = msg['param_id']
            param_value = msg['param_value']
            
            if param_id == 'BAT_LOW_THR':
                self.low_battery_threshold = param_value
                logging.info("BAT_LOW_THR: {0}".format(self.low_battery_threshold))
            elif param_id == 'BAT_CRIT_THR':
                self.critical_battery_threshold = param_value
                logging.info("BAT_CRIT_THR: {0}".format(self.critical_battery_threshold))
            elif param_id == 'BAT_EMERGEN_THR':
                self.emergency_battery_threshold = param_value
                logging.info("BAT_EMERGEN_THR: {0}".format(self.emergency_battery_threshold))
            elif param_id == 'BAT_AVRG_CURRENT':
                self.average_current = param_value
                logging.info("BAT_AVRG_CURRENT: {0}".format(self.average_current))
            elif param_id == 'BAT1_N_CELLS':
                self.num_battery_cells = param_value
                logging.info("BAT1_N_CELLS: {0}".format(self.num_battery_cells))
            elif param_id == 'BAT1_V_DIV':
                self.voltage_divider = param_value
                logging.info("BAT1_V_DIV: {0}".format(self.voltage_divider))
            elif param_id == 'BAT1_V_EMPTY':
                self.voltage_empty = param_value
                logging.info("BAT1_V_EMPTY: {0}".format(self.voltage_empty))
            elif param_id == 'BAT1_R_INTERNAL':
                self.internal_resistance = param_value
                logging.info("BAT1_R_INTERNAL: {0}".format(self.internal_resistance))
            elif param_id == 'BAT1_CAPACITY':
                self.battery_capacity_mAh = param_value
                logging.info("BAT1_CAPACITY: {0}".format(self.battery_capacity_mAh))
            elif param_id == 'BAT1_I_CHANNEL':
                self.current_channel = param_value
                logging.info("BAT1_I_CHANNEL: {0}".format(self.current_channel))
            elif param_id == 'BAT1_SOURCE':
                self.battery_source = param_value
                logging.info("BAT1_SOURCE: {0}".format(self.battery_source))
            elif param_id == 'BAT1_V_CHANNEL':
                self.voltage_channel = param_value
                logging.info("BAT1_V_CHANNEL: {0}".format(self.voltage_channel))
            elif param_id == 'BAT1_V_CHARGED':
                self.voltage_charged = param_value
                logging.info("BAT1_V_CHARGED: {0}".format(self.voltage_charged))
            elif param_id == 'BAT1_V_LOAD_DROP':
                self.voltage_load_drop = param_value
                logging.info("BAT1_V_LOAD_DROP: {0}".format(self.voltage_load_drop))
            elif param_id == 'BAT1_V_LOAD_REF':
                self.voltage_load_ref = param_value
                logging.info("BAT1_V_LOAD_REF: {0}".format(self.voltage_load_ref))             
                
    def create_battery_status_message(self):
        '''
        Creates a BATTERY_STATUS MAVLink message with the current state of the virtual battery.
        '''
        battery_status_message = self.message_set.create('BATTERY_STATUS')
        battery_status_message.set_from_dict({
            'id': 0, 
            'battery_function': message_set.enum('MAV_BATTERY_FUNCTION_ALL'),
            'type': message_set.enum('MAV_BATTERY_TYPE_LIPO'),
            'temperature': 25,  
            'voltages': [int(self.voltage_battery_v * 1000)] + [65535] * 9, 
            'current_battery': int(self.current_battery_a * 100),  
            'current_consumed': self.energy_consumed_mAh,
            'energy_consumed': int(self.energy_consumed_mAh),  
            'battery_remaining': self.battery_remaining,  
        })
        return battery_status_message


if __name__ == "__main__":

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.INFO)

    message_set = libmav.MessageSet('./mavlink/common.xml')
    
    heartbeat = message_set.create('HEARTBEAT').set_from_dict({
        'type': message_set.enum('MAV_TYPE_BATTERY'),
        'autopilot': message_set.enum('MAV_AUTOPILOT_INVALID'),
        'base_mode': 0,
        'custom_mode': 0,
        'system_status': message_set.enum('MAV_STATE_ACTIVE')
    })

    system_id = 1
    mavlink_identifier = libmav.Identifier(
        system_id, message_set.enum('MAV_COMP_ID_BATTERY'))

    conn_physical = libmav.TCPClient(
        '172.17.0.1', 5790)  
    conn_runtime = libmav.NetworkRuntime(
        mavlink_identifier, message_set, heartbeat, conn_physical)

    virtual_battery = VirtualBattery(message_set)

    last_battery_status_update_t = 0

    while True:
        if virtual_battery.connection is None or not virtual_battery.connection.alive():
            try:
                virtual_battery.connection = conn_runtime.await_connection(2000)
                logging.info("MAVLink connected")
                
                callback_handle = virtual_battery.connection.add_message_callback(
                    virtual_battery.handle_param_value_message)
                
                param_request_msg = message_set.create('PARAM_REQUEST_LIST').set_from_dict({
                    'target_system': 1,
                    'target_component': 1,
                })
                virtual_battery.connection.send(param_request_msg)
                
            except RuntimeError:
                logging.info("{0} Waiting for connection...".format(datetime.datetime.now()))
                continue

        virtual_battery.update_state()

        if time.time() - last_battery_status_update_t > 1:
            battery_status_msg = virtual_battery.create_battery_status_message()
            #logging.info(battery_status_msg)
            virtual_battery.connection.send(battery_status_msg)
            last_battery_status_update_t = time.time()
