#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from SysLib import*
#plt.rcParams["figure.figsize"] = (10,5)
pcv.params.debug = 'none'


# In[ ]:


m=CreateMainFolder()
print("Experiment:",m)
ExperimentNr='Experiment'+'_'+str(m)
NewPositionsList=[["0","X",8,"D","Y",59],["1","X",7,"D","Y",191],["2","X",131,"D","Y",59],["3","X",125,"D","Y",192],["4","X",250,"D","Y",60],["5","X",249,"D","Y",190],["6","X",372,"D","Y",65],["7","X",369,"D","Y",198],["8","X",500,"D","Y",65],["9","X",494,"D","Y",195]]#,["10","X",615,"D","Y",58],["11","X",610,"D","Y",193]]
#if not NewPositionsList:
#    Scan(ExperimentNr)
if not FinalList:
    ProduceFinalList(NewPositionsList,NewPositionsListallOther,m)
    FinalList=finalList
    VisulizeCirclesPlot(FinalList,m)
if not PlantList:
    GoToNewPositionStoredinList(FinalList,m)
    VisulizeCircles_PlantPlot(FinalList,PlantList,m)
GetTimeLapseData(FinalList,m,0,0,RGB=True,SPECTRAL=True,DEPTH=True)
#MultiSensorData()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




