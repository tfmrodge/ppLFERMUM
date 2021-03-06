# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 14:17:51 2018
def backward_calc(self,ic,num_compartments,target_conc = 1,target_emiss = 1):
@author: Tim Rodgers
"""
import numpy as np
import pandas as pd
num_compartments = 7
target_emiss = 1
target_conc = 3

#Initialize outputs
col_name = pd.Series(index = range(num_compartments))
for i in range(num_compartments):
    col_name[i] = 'f'+str(i+1) #Fugacity for every compartment
#Emissions for the target_emiss compartment
col_name[num_compartments+1] = 'emiss_'+str(target_emiss)
bw_out = pd.DataFrame(index = ic['Compound'],columns = col_name)        
#Define target name and check if there is a value for it in the ic dataframe. If not, abort
targ_name = 'targ_' + str(target_conc)

#initialize a matrix of (numc - 1) x numc compartments. This is not necessarily a determined system
D_mat = pd.DataFrame(index = range(num_compartments-1),columns = range(num_compartments))
#initialize a blank dataframe for input vectors, RHS of matrix.
inp_val = pd.DataFrame(index = range(num_compartments-1),columns = ic.Compound)
#Loop over the chemicals, solving for each.
for chem in ic.index: #Index of chemical i starting at 0
    #Put the target fugacity into the output
    bw_out.iloc[chem,target_conc] = ic.loc[chem,targ_name]
    #Double loop to set matrix values
    j = 0 #Index to pull values from ic
    jj = 0 #Index to fill matrix
    while j < num_compartments: #compartment j, index of D_mat
        #Skip the target_conc row as we know f(T)
        if (j+1) == target_conc:
            j += 1
        #Define RHS = -Inp(j) - D(Tj)*f(T) for every compartment j using target T
        D_val = 'D_' +str(target_conc)+str(j+1) #label compartments from 1
        inp_name = 'inp_' + str(j + 1) #must have an input for every compartment, even if it is zero
        if D_val in ic.columns: #check if there is a D(Tj) value
            if j+1 == target_emiss: #Set -Inp(j) to zero for the targ_emiss row, we will subtract GCb(target_emiss) later
                inp_val.iloc[jj,chem] = -ic.loc[chem,D_val] * bw_out.iloc[chem,target_conc]
            else:
                inp_val.iloc[jj,chem] = -ic.loc[chem,inp_name] - ic.loc[chem,D_val]*bw_out.iloc[chem,target_conc]
        else: #If there is no D(Tj) then RHS = -Inp(j), unless it is the target_emiss column again
            if j+1 == target_emiss: 
                inp_val.iloc[jj,chem] = 0
            else:
                inp_val.iloc[jj,chem] = i-ic.loc[chem,inp_name]
  
        #Set D values across each row
        k = 0 #Compartment index
        kk = 0 #Index to fill matrix
        while k < num_compartments: #compartment k, column of D_mat
            if (k+1) == target_conc:
                k += 1
            if j == k:
                DT = 'DT' + str(j + 1)
                D_mat.iloc[jj,kk] = -ic.loc[chem,DT]
            else:
                D_val = 'D_' +str(k+1)+str(j+1) #label compartments from 1
                if D_val in ic.columns: #Check if there is transfer between the two compartments
                    D_mat.iloc[jj,kk] = ic.loc[chem,D_val]
                else:
                    D_mat.iloc[jj,kk] = 0 #If no transfer, set to 0
            if k+1 == num_compartments: #Final column is the input to the target_emiss compartment
                if (j+1) == target_emiss: #This is 1 for the target_emiss column and 0 everywhere else
                    D_mat.iloc[jj,kk+1] = 1
                else:
                    D_mat.iloc[jj,kk+1] = 0
            k +=1
            kk += 1
        j += 1
        jj += 1
    #Solve for fugsinp = D_mat\inp_val, the last value in fugs is the total inputs
    lhs = np.array(D_mat,dtype = float)
    rhs = np.array(inp_val.iloc[:,chem],dtype = float)
    fugsinp = np.linalg.lstsq(lhs,rhs,rcond = None)
    bw_out.iloc[chem,:] = fugsinp
