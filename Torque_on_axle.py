
import pandas as pd
import numpy as np
import os
# import plotly.express as px
import plotly.graph_objects as go
from scipy.signal import find_peaks
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt

Files_path = r"C:\Users\kjl\OneDrive - Jongia NV\Bureaublad\Calibration_testing\Torque\Short"
# Files_path = r"C:\Users\kjl\OneDrive - Jongia NV\Bureaublad\Calibration_testing\Torque\Long"


# def Calibration_deflection(Files_path):
files = os.listdir(Files_path)
file_names = []
Torque = []
Results = []
for file in files:

    if "50Nm" in files:
        break
    fig = go.Figure()
    # print(file[-3:])
    file_path = os.path.join(Files_path, file)
    # print(file_path)
    file_names.append(file)
    file = file.replace(",", ".")
    list_name = list(file.split("__"))

    # print(list_name)
    Torque.append(list_name[-1][0:-2])
    Torque = [float(x) for x in Torque]



    file_path = os.path.join(Files_path, file)

    df = pd.read_feather(file_path)
    df = df.drop(['Time_stamp', 'Seqnr', 'Sync_status', 'TEC_status', 'Channel_nr', 'Sensor_nr'], axis=1)
    df = df.drop_duplicates(["Gator_Timestamp"])

    df.iloc[:, 1:9] = df.iloc[:, 1:9] / 1000
    df = df.drop(["Gator_Timestamp"], axis=1)
    df = df[20:]
    df = df.reset_index(inplace=False, drop=True)
    print("")
    df.rename(columns={'Gator_Timestamp': "Gator_timestamp", 'Wavelength_1': "Temp_RVS",
                       'Wavelength_2': "AX1", 'Wavelength_3': "Tor1", 'Wavelength_4': "AX2", 'Wavelength_5': "AX3",
                       'Wavelength_6': "Tor2", 'Wavelength_7': "AX4", 'Wavelength_8': "Temp_air"}, inplace=True)
    df2 = df

    df2.columns = ["Temp_RVS", "AX1", "Tor1", "AX2", "AX3", "Tor2", "AX4", "Temp_air"]

    Lambda_0_Tor1 = df2.loc[0, "Tor1"]
    Lambda_0_Tor2 = df2.loc[0, "Tor2"]
    print("")
    # Calculates the Strain of each individual Ax sensor
    df2["Tor1"] = ((df2.loc[:, "Tor1"] - Lambda_0_Tor1) / Lambda_0_Tor1 * 0.78) * 1000000
    df2["Tor2"] = ((df2.loc[:, "Tor2"] - Lambda_0_Tor2) / Lambda_0_Tor2 * 0.78) * 1000000
    df2["Tor"] = (df2["Tor1"] - df2["Tor2"])/2

    print("")
    thresh = 50
    peaks = find_peaks(-df2["Tor"], height=thresh, distance=1000)

    peaks = list(zip(peaks[0], peaks[1]["peak_heights"]))
    df_peaks = pd.DataFrame(peaks, columns=["index", "peaks"])
    df_peaks["peaks"] = -1 * df_peaks["peaks"]
    df_peaks.set_index("index", inplace=True, drop=True)

    df2 = df2.join(df_peaks)
    # df_peak= pd.DataFrame(peaks[1])

    # print("")
    print_list = ["Tor", "peaks"]

    for column in print_list:
        fig.add_trace(go.Scattergl(x=df2.index, y=df2[column],
                                   mode="markers",
                                   name=f"{file}",
                                   showlegend=True))

    fig.show()
    peaks_list = [x[1] for x in peaks]
    sum_peaks = sum(peaks_list)
    len_peaks = len(peaks_list)
    avg = sum_peaks / len_peaks
    Results.append((int(list_name[-1][0:-2]), avg))

df_results = pd.DataFrame(Results, columns=["torque", "strain"])
Function = np.polyfit(df_results["strain"], df_results["torque"], 1, full=True)
df_results["torque_calc"] = Function[0][0] * df_results["strain"] + Function[0][1]

df_results.plot("torque", "strain", kind='scatter')
plt.show()

R2_a = r2_score(df_results["torque"], df_results["torque_calc"])

A_Torque = Function[0][0]
B_Torque = Function[0][1]

R2_torque = r2_score(df_results["torque"], df_results["torque_calc"])

print(f"Torque function will be {A_Torque}*x + {B_Torque}")
print("")
print(f"R^2 value of torque is {R2_torque}")

print("")






# Func_force = np.polyfit(df2["AX_Avg"], df2["Force"], 1, full=True)
# Func_deflec = np.polyfit(df2["AX_Avg"], df2["Deflection"], 1, full=True)
# df2["Force_calc"] = Func_force[0][0] * df2["AX_Avg"] + Func_force[0][1]
# df2["Deflection_calc"] = Func_deflec[0][0] * df2["AX_Avg"] + Func_deflec[0][1]


#Calculate distribution over sensors.
# df2['total_Strain'] = df2["AX1"] + df2["AX2"] + df2["AX3"] + df2["AX4"]
# for n in range(0, len(df2["AX_Avg_temp"])):
#     print("")
#     print((df2["AX1"][n]/df2['total_Strain'][n])*100, (df2["AX2"][n]/df2['total_Strain'][n] )*100, (df2["AX3"][n]/df2['total_Strain'][n])*100, (df2["AX4"][n]/df2['total_Strain'][n])*100)
    # print(((df2["AX1"][n]/df2['total_Strain'][n])*100)+(df2["AX2"][n]/df2['total_Strain'][n]*100)+((df2["AX3"][n]/df2['total_Strain'][n])*100)+((df2["AX4"][n]/df2['total_Strain'][n])*100))

# Function2 = np.polyfit(df2["AX_Avg_temp"], df2["Weights"], 1, full=True)
# df2["Weights_calc_temp"] = Function2[0][0] * df2["AX_Avg"] + Function2[0][1]
#
# A_force = Func_force[0][0]
# B_force = Func_force[0][1]
#
# A_deflection = Func_deflec[0][0]
# B_deflection = Func_deflec[0][1]
#
# R2_force = r2_score(df2["Force"], df2["Force_calc"])
# R2_deflection = r2_score(df2["Deflection"], df2["Deflection_calc"])
#
# print(f"Force function will be {A_force}*x + {B_force}")
# print(f"Deflection function will be {A_deflection}*x + {B_deflection}")
# print("")
# print(f"R^2 value of Axe_avg force is {R2_force}")
# print(f"R^2 value of Axe_avg deflection is {R2_deflection}")

# R2_b = r2_score(df2["Weights"], df2["Weights_calc_temp"])

# df.plot(x = df2["AX1"], y = df2.index)
# df.index.plot.line(x = "AX1")
# df2.plot("AX_Avg", "Force", kind = 'scatter')
# plt.show()
#
# print("")
# df2.plot("AX_Avg", "Deflection", kind = 'scatter')
# plt.show()
# df = df.rename(index = Weights)
# for n in Weights:
# print(df.columns)

# I need to return the Lambda_0's,



