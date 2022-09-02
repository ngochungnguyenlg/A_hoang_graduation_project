from unittest import result
import pandas as pd
from crawlerdatata_final_v import *
from sklearn import model_selection
import pickle
import copy
import re

df = pd.read_excel(
    '.\model\Testing.xlsx') 
df.columns = df.iloc[0, :]
df = df.drop(0)  

clm = list(df.columns)  

start_clm_idx = clm.index('2. Persistent Bioaccumulative Toxic')
end_clm_idx = clm.index('18. WaterSense') 
original_clm = clm[start_clm_idx:end_clm_idx+1] 


dict_model = {  # model dictionary
    '2. Persistent Bioaccumulative Toxic': '2. No Lead, Cadmium, and Copper_SVM.sav',
    '3. Cradle to Gate': '3. Cradle to Gate_RF.sav',
    '4. Cradle to Grave': '4. Cradle to Grave_RF.sav',
    '5. Environmental Product Declarations (EPD)': '5. Environmental Product Declarations (EPD)_SVM.sav',
    '6. Corporate sustainability reports (CSR)': '6. Corporate sustainability reports (CSR)_SVM_pred.sav',
    '7. Extended producer responsibility  (EPR)': '7. Extended producer responsibility (EPR)_SVM.sav',
    '8. Reporting ﻿U.N. Global Compact': '8. N. Global Compact_SVM.sav',
    '9. Certificate FSC': '9. Certificate FSC_NB.sav',
    '10. Recycled content': '10. Recycled content_SVM.sav',
    '11. Health Product Declaration': '11. Health Product Declaration_kNN.sav',
    '12. Cradle to Cradle': '12. Cradle to Cradle_RF.sav',
    '13. Green Screen': '13. Green Screen_SVM.sav',
    '15. VOC': '15. Low-Emitting Materials_RF.sav',
    '16. ENERGY STAR ': '16. ENERGY STAR _SVM.sav',
    '17. EPEAT': '17. EPEAT_RF.sav',
    '18. WaterSense': '18. WaterSense_kNN.sav',
}



if __name__ == '__main__':
    maxprocess = 5
    maxThread = 5
    df_write = copy.deepcopy(df)

    for head in original_clm:
        current_columns = list(df_write.columns)
        current_idx_clm = current_columns.index(head)
        df_write.insert(current_idx_clm+1, head+'_output', 'unknown')
    step = 100  # muc do chia nho file
    time.sleep(0.5)
    p = []
    cnt = 1
    for i in range(0, len(df_write), step):  # vi tri start
        if(i+step > len(df)):
            step = len(df)-i

        df_run = df_write.iloc[i:i+step, :]
        df_run = df_run.reset_index(drop=True)
        name = str(i)+'_'+str(i+step)+'_'+gettime()
        
        process_call = Process_(maxThread, name, dict_model)
        process_i = multiprocessing.Process(
            target=process_call.running_fuc, args=(df_run, name, original_clm))
        process_i.start()

        p.append(process_i)
        if cnt == maxprocess:
            for j in range(maxprocess):
                p[j].join()
                cnt = 1
            p.clear()
        else:
            cnt += 1
