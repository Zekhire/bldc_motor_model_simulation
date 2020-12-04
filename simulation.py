import bldc_motor_model_kk
import pi_controller
import json
import numpy as np
import matplotlib.pyplot as plt

import time


class Simulation:
    def __init__(self, bldc_motor_data, pi_controller_data):
        self.bldc_motor    = bldc_motor_model_kk.BLDC_Motor(bldc_motor_data)
        self.pi_controller = pi_controller.PI_Controller(pi_controller_data)

        # Simulation parameters
        self.dt = 0.01
        self.iterations = 10000
        t = np.ones(self.iterations)
        t = t*self.dt
        t = np.cumsum(t)
        t = t-self.dt
        self.t = t

        self.w_ref = np.append(40*np.ones(int(self.iterations/2)), 10*np.ones(int(self.iterations/2)))
        self.T_l   = 0*np.ones(self.iterations)

        self.simulation_output = {}


    def run_simulation(self, noise=False):
        self.w_m = np.zeros(self.iterations)
        self.i_a = np.zeros(self.iterations)
        self.i_b = np.zeros(self.iterations)
        self.i_c = np.zeros(self.iterations)
        self.T_e = np.zeros(self.iterations)
        self.v_a = np.zeros(self.iterations)
        self.v_b = np.zeros(self.iterations)
        self.v_c = np.zeros(self.iterations)
        self.v_s = np.zeros(self.iterations)

        # Simulation main loop
        for i in range(self.iterations):
            if i%1000 == 0:
                print(str((i/self.iterations)*100)+"%")

            # Feedback loop sum block
            if i == 0:
                e = self.w_ref[i]
            else:
                e = self.w_ref[i] - self.w_m[i-1]
                
            # PI controller block
            u_dict = {"e": np.array([e])}
            y_dict_pi_controller = self.pi_controller.simulation_euler_anti_windup(self.dt, 1, u_dict)
            self.v_s[i] = y_dict_pi_controller["y"][0]

            # BLDC motor
            u_dict = {"v_s": np.array([self.v_s[i]]), 
                      "T_l": np.array([self.T_l[i]])}

            y_dict_dc_motor = self.bldc_motor.simulation_euler(self.dt, 1, u_dict)

            self.w_m[i] = y_dict_dc_motor["w_m"][0]
            self.i_a[i] = y_dict_dc_motor["i_a"][0]
            self.i_b[i] = y_dict_dc_motor["i_b"][0]
            self.i_c[i] = y_dict_dc_motor["i_c"][0]
            self.v_a[i] = y_dict_dc_motor["v_a"][0]
            self.v_b[i] = y_dict_dc_motor["v_b"][0]
            self.v_c[i] = y_dict_dc_motor["v_c"][0]
            self.T_e[i] = y_dict_dc_motor["T_e"][0]

            if noise:
                noise = np.random.normal(0, .1)
                self.w_m[i] += noise

        self.simulation_output = {
            "w_m": self.w_m,        
            "i_a": self.i_a,                         # \
            "i_b": self.i_b,                         # - plot
            "i_c": self.i_c,                         # /
            "v_a": self.v_a,                         # - plot
            "v_b": self.v_b,                         # - plot
            "v_c": self.v_c,                         # - plot
            "T_e": self.T_e,                         # - plot
        }
        
        return self.simulation_output, self.t


if __name__ == "__main__":
    bldc_motor_data_path    = "./bldc_motor_data_kk.json"
    pi_controller_data_path = "./pi_controller_data.json"
    bldc_motor_data         = json.load(open(bldc_motor_data_path))
    pi_controller_data      = json.load(open(pi_controller_data_path))

    simulation = Simulation(bldc_motor_data, pi_controller_data)
    simulation_output_def, t_meas = simulation.run_simulation(noise=False)

    # plot speed
    ylim_coeff = 1.2
    plt.plot(t_meas, simulation.w_ref, "-r", label="ωref")
    plt.plot(t_meas, simulation_output_def["w_m"], "-b", label="ωm")
    plt.xlim([0, t_meas[-1]])
    plt.ylim([np.min(simulation_output_def["w_m"])*ylim_coeff, np.max(simulation_output_def["w_m"])*ylim_coeff])
    plt.xlabel("t[s]")
    plt.ylabel("ω[rad/s]")
    plt.legend(loc="right")
    plt.grid(which="both")
    plt.minorticks_on()
    plt.show()
