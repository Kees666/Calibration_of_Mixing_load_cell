
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score


Files_path = r"C:\Users\kjl\OneDrive - Jongia NV\Bureaublad\Calibration_testing\Weight"

def Calibration_torque(Files_path):
    files = os.listdir(Files_path)
    file_names = []
    force = []
    for file in files:

        # print(file[-3:])
        file_path = os.path.join(Files_path, file)
        # print(file_path)
        file_names.append(file)
        file = file.replace(",", ".")
        list_name = list(file.split("_"))
        # print(list_name)
        force.append(list_name[-1][0:-1])

        is_CSV = False
        # print(os.path.getmtime(file_path))
    print("")
    if force[0] != "0":
        force = force[::-1]

    file_path = os.path.join(Files_path, file)
    # print(file_path)
    df = pd.read_feather(file_path)
    df = df.drop(['Time_stamp', 'Seqnr', 'Sync_status', 'TEC_status', 'Channel_nr', 'Sensor_nr'], axis=1)
    df = df.drop_duplicates(["Gator_Timestamp"])

    df.iloc[:, 1:9] = df.iloc[:, 1:9] / 1000
    df = df.drop(["Gator_Timestamp"], axis=1)
    df = df[20:]

def Calibration_Thrust(Files_path):
    files = os.listdir(Files_path)
    file_names = []
    Weights = []
    for file in files:

        # print(file[-3:])
        if file[-3:] == "csv":
            file_path = os.path.join(Files_path, file)
            # print(file_path)
            file_names.append(file)
            file = file.replace(",", ".")
            list_name = list(file.split("_"))
            # print(list_name)
            Weights.append(list_name[-1][0:-5])
            is_CSV = True
        else:

            file_path = os.path.join(Files_path, file)
            # print(file_path)
            file_names.append(file)
            file = file.replace(",", ".")
            list_name = list(file.split("_"))
            # print(list_name)
            Weights.append(list_name[-1][0:-1])

            is_CSV = False
            # print(os.path.getmtime(file_path))
    print("")
    if Weights[0] != "0":
        Weights = Weights[::-1]


    Weights = [float(x) for x in Weights]
    Weights[0] = 0
    print(Weights)
    # print("test")

    Results = []

    for file in files:
    # Path of the folder with the calibration files
        file_path = os.path.join(Files_path, file)
        # print(file_path)
        if not is_CSV:
            df = pd.read_feather(file_path)
        else:
            df = pd.read_csv(file_path)
        df = df.drop(['Time_stamp', 'Seqnr', 'Sync_status', 'TEC_status', 'Channel_nr', 'Sensor_nr'], axis=1)
        df = df.drop_duplicates(["Gator_Timestamp"])

        # res = (df.groupby((df.Label != ).cumsum()).mean().reset_index(drop=True))
        # df = df.iloc[::5, :]
        # df = df.reset_index(drop = True, inplace = False)
        # I changed the last nr by removing 1 zero, I am averaging over 10 measurements so dt is now larger.
        # diff between two measurments in microseconds devided by 1*10^6 to get seconds.

        df.iloc[:, 1:9] = df.iloc[:, 1:9] / 1000
        df = df.drop(["Gator_Timestamp"], axis=1)
        df = df[20:]
        # print(file)
        Mean_values = {}
        # print("")
        for n in range(df.shape[1]):
            # print(df.columns[n])
            # print(df[df.columns[n]].mean())
            Mean_values[df.columns[n]] = df[df.columns[n]][100:].mean()
            # print(Mean_values)
        Results.append(Mean_values)

    df2 = pd.DataFrame(Results)

    df2.columns = ["Temp_RVS", "AX1", "Tor1", "AX2", "AX3", "Tor2", "AX4", "Temp_air"]
    df2["Weights"] = Weights
    print("")
    # print(df.loc[:, "AX1"])
    Lambda_0_AX1 = df2.loc[0, "AX1"]
    Lambda_0_AX2 = df2.loc[0, "AX2"]
    Lambda_0_AX3 = df2.loc[0, "AX3"]
    Lambda_0_AX4 = df2.loc[0, "AX4"]
    Lambda_0_Temp_AST = df2.loc[0, "Temp_RVS"]

    # Calculates the Strain of each individual Ax sensor
    df2["AX1"] = ((df2.loc[:, "AX1"] - Lambda_0_AX1) / Lambda_0_AX1 * 0.78) * 1000000
    df2["AX2"] = ((df2.loc[:, "AX2"] - Lambda_0_AX2) / Lambda_0_AX2 * 0.78) * 1000000
    df2["AX3"] = ((df2.loc[:, "AX3"] - Lambda_0_AX3) / Lambda_0_AX3 * 0.78) * 1000000
    df2["AX4"] = ((df2.loc[:, "AX4"] - Lambda_0_AX4) / Lambda_0_AX4 * 0.78) * 1000000
    df2["Temp_RVS"] = ((df2.loc[:, "Temp_RVS"] - Lambda_0_Temp_AST) / Lambda_0_Temp_AST * 0.78) * 1000000  # this is now strain of Temp_RVS

    df2["AX_Avg"] = (df2["AX1"] + df2["AX3"] + df2["AX3"] + df2["AX4"]) / 4
    df2["AX_Avg_temp"] = df2["AX_Avg"].sub(df2["Temp_RVS"], axis=0)

    print("")
    Function = np.polyfit(df2["AX_Avg"], df2["Weights"], 1, full=True)
    df2["Weights_calc"] = Function[0][0] * df2["AX_Avg"] + Function[0][1]
    print("")
    #Calculate distribution over sensors.
    df2['total_Strain'] = df2["AX1"] + df2["AX2"] + df2["AX3"] + df2["AX4"]
    # for n in range(0, len(df2["AX_Avg_temp"])):
    #     print("")
    #     print((df2["AX1"][n]/df2['total_Strain'][n])*100, (df2["AX2"][n]/df2['total_Strain'][n] )*100, (df2["AX3"][n]/df2['total_Strain'][n])*100, (df2["AX4"][n]/df2['total_Strain'][n])*100)
        # print(((df2["AX1"][n]/df2['total_Strain'][n])*100)+(df2["AX2"][n]/df2['total_Strain'][n]*100)+((df2["AX3"][n]/df2['total_Strain'][n])*100)+((df2["AX4"][n]/df2['total_Strain'][n])*100))

    # Function2 = np.polyfit(df2["AX_Avg_temp"], df2["Weights"], 1, full=True)
    # df2["Weights_calc_temp"] = Function2[0][0] * df2["AX_Avg"] + Function2[0][1]

    R2_a = r2_score(df2["Weights"], df2["Weights_calc"])
    # R2_b = r2_score(df2["Weights"], df2["Weights_calc_temp"])

    # df.plot(x = df2["AX1"], y = df2.index)
    # df.index.plot.line(x = "AX1")
    df2.plot("AX_Avg", "Weights", kind = 'scatter')

    plt.show()
    # df = df.rename(index = Weights)
    # for n in Weights:
    # print(df.columns)
    print(f"R^2 value of Axe_avg is {R2_a}")
    # I need to return the Lambda_0's,

    return Function[0][0], Function[0][1], Lambda_0_AX1, Lambda_0_AX2, Lambda_0_AX3, Lambda_0_AX4, Lambda_0_Temp_AST

A, B, Lambda_0_AX1, Lambda_0_AX2, Lambda_0_AX3, Lambda_0_AX4, Lambda_0_Temp_AST = Calibration_Thrust(Files_path)
print(f" A= {A}, B= {B}, so Thrust will be y = {A}*x + {B}")

