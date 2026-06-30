# The HEAD over HEELS project (fluid-level plasma analysis, not full kinetic analysis)

import numpy as np
import matplotlib.pyplot as plt
import spacepy
import spacepy.pycdf as pycdf
import os 
from spacepy.pycdf import lib

# Here we define the signal processing functions

def moving_average(x, window=1000):
    return np.convolve(x, np.ones(window)/window, mode='same')   # this one is for noise reduction 

# Here we define the datasets

EDP_file = "/home/anac_dias/myenv/Codes/MMS_20180212/EDP_FAST.cdf"
FPI_file = "/home/anac_dias/myenv/Codes/MMS_20180212/FPI_FAST_06.cdf"
FGM_file = "/home/anac_dias/myenv/Codes/MMS_20180212/FGM_SRVY.cdf"

# Check if files exist
print("EDP exists:", os.path.exists(EDP_file))
print("FPI exists:", os.path.exists(FPI_file))
print("FGM exists:", os.path.exists(FGM_file))

# Let's open the files
EDP = pycdf.CDF(EDP_file)
FPI = pycdf.CDF(FPI_file)
FGM = pycdf.CDF(FGM_file)

print("All datasets are open, dude")

# Time to inspect the variables

print("\nEDP variables are:")
print(EDP.keys())

print("\nFPI variables are:")
print(FPI.keys())

print("\nFGM variables are:")
print(FGM.keys())

print("Variables were inspected, dude")

# Time to define the variables based on the output 

B = FGM['mms1_fgm_b_gse_srvy_l2'][...]                    #['Epoch'] detects if variable is a time format and converts the array of int into datetime
time_FGM = FGM['Epoch'][...]                              # Quick info: no need to convert to datetime
                                                          
Bx = B[:, 0]
By = B[:, 1]
Bz = B[:, 2]
B_mag = B[:, 3]

Ni = FPI['mms1_dis_numberdensity_fast'][...]
time_FPI = FPI['Epoch'][...]

V = FPI['mms1_dis_bulkv_gse_fast'][...]
Vx = V[:, 0]
Vy = V[:, 1]
Vz = V[:, 2]

E = EDP['mms1_edp_dce_gse_fast_l2'][...]
time_EDP = EDP['mms1_edp_epoch_fast_l2'][...]

Ex = E[:, 0]
Ey = E[:, 1]
Ez = E[:, 2]

print("Variables defined and ready to go")

# A little checkpoint: I'm checking the dimensions of the variables
print("First FGM time object:", type(time_FGM[0]))
print(B.shape)
print(Ni.shape)
print(E.shape)

# Now, we do math: Magnetic field magnitude

B_mean = np.mean(B_mag)

# Fluctuations check here

delta_B = B_mag - B_mean
deltaB_over_B = delta_B / B_mean
print("Mean B:", B_mean)

# Applying the smoothing effect on the data

B_smooth = moving_average(B_mag, window=5000)          # Tip: very high resolution = needs more smoothing
Ni_smooth = moving_average(Ni, window=50)
Vx_smooth = moving_average(Vx, window=50)

print("Smoothing the data now")

# Now, we compute the gradients and how they are changing (derive that shit)

dB_dt = np.gradient(B_smooth)
dn_dt = np.gradient(Ni_smooth)
dVx_dt = np.gradient(Vx_smooth)

# Allow me to set up the shock conditions to be recognized 

shock_cond = (B_smooth > 3*np.mean(B_smooth)) & (deltaB_over_B > 0.5)
density_jump = Ni_smooth > 2 * np.mean(Ni_smooth)
velocity_drop = Vx_smooth > -300                    # Remember: these values are set up upon looking at the test script, dude (ALWAYS RUN THE TEST CODE FIRST)
shock_indices = np.where(shock_cond)[0]

# Here we extract the shock time window, dude

if len(shock_indices) > 0:
    shock_time = time_FGM[shock_indices[0]]
    print("HERE, LOOK! Shock detected at:", shock_time)
else:
    print("Damn. No shock detected, dude")


# Component correlations 

corr_B = np.corrcoef(np.vstack((Bx, By, Bz)))
corr_E = np.corrcoef(np.vstack((Ex, Ey, Ez)))

print("Correlation B:\n", corr_B)
print("Correlation E:\n", corr_E)

# Now, we plot

step = 1000  # downsampling for speed

plt.figure(figsize=(10,6))
plt.plot(time_FGM[::step], B_mag[::step], label='|B|')

plt.scatter(time_FGM[shock_indices], B_mag[shock_indices],      # Overlaying the shock points
            color='red', s=10, label='Detected Shock')

plt.title("Magnetic Field Magnitude")
plt.ylabel("nT")
plt.legend()
plt.grid()


plt.figure(figsize=(10,6))
plt.plot(time_FPI, Ni, label='Ion Density')
plt.ylabel("cm^-3")
plt.title("Ion Density")
plt.legend()
plt.grid()


plt.figure(figsize=(10,6))
plt.plot(time_FPI, Vx, label='Vx')
plt.plot(time_FPI, Vy, label='Vy')
plt.plot(time_FPI, Vz, label='Vz')
plt.title("Ion Velocity Components")
plt.ylabel("km/s")
plt.legend()
plt.grid()


plt.figure(figsize=(10,6))
plt.plot(time_EDP[::step], Ex[::step], label='Ex')
plt.plot(time_EDP[::step], Ey[::step], label='Ey')
plt.plot(time_EDP[::step], Ez[::step], label='Ez')
plt.title("Electric Field Components")
plt.ylabel("mV/m")
plt.legend()
plt.grid()


plt.figure(figsize=(10,6))
plt.plot(time_FGM[::step], deltaB_over_B[::step], label='δB/B')

plt.scatter(time_FGM[shock_indices], deltaB_over_B[shock_indices],
            color='red', s=10)

plt.title("Magnetic Field Fluctuation")
plt.legend()
plt.grid()

plt.show()

print("All plots were generated, dude")