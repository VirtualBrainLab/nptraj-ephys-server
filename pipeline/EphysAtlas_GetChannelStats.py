from one.api import ONE
one = ONE(base_url='https://alyx.internationalbrainlab.org',cache_dir='D:\\FlatIron')
import brainbox.io.one as bbone
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
from brainbox.io.one import SpikeSortingLoader
from ibllib.atlas import AllenAtlas
atlas = AllenAtlas(25)

# For testing
with open("bwm_eid.pkl",'rb') as f:
    ins = pickle.load(f)
    
# Setup the log spacing we'll use to save the ISI distribution
logbins = np.logspace(np.log10(0.001),np.log10(10),10)
logbins = np.insert(logbins,0,0)

# Now run through every *channel* in the data, saving the spike distribution and 

for insertion in ins:
  eid = insertion[0]
  probe = insertion[1]
  print("Starting: " + eid)
  # create a new pandas dataframe
  insertions = one.alyx.rest('insertions', 'list', session=eid)

  try:
    passivePeriods = one.load_dataset(eid,'alf/_ibl_passivePeriods.intervalsTable.csv')
  except:
    continue
  spontStart = passivePeriods['spontaneousActivity'][0]
  spontEnd = passivePeriods['spontaneousActivity'][1]

  pids = [i['id'] for i in insertions]
  for pid in pids:
    df = pd.DataFrame(columns =['channel','ml','ap','dv','atlas_id','clu_count','amp_min','amp_max',*logbins[1:]])
    ssl = SpikeSortingLoader(pid=pid, one=one)
    spikes, clusters, channels = ssl.load_spike_sorting()

    if 'x' not in channels.keys():
      continue

    clu = spikes.clusters
    st = spikes.times

    # convert clu to cha 
    cha = clusters.channels[clu]
    ucha = np.unique(cha)

    # get the list of clusters for each channel
    chaCluDict = {}
    for i,ch in enumerate(clusters.channels):
      if (ch in chaCluDict.keys()):
        chaCluDict[ch].append(i)
      else:
        chaCluDict[ch] = [i]

    for i,ch in enumerate(ucha):
      st_idxs = np.argwhere((cha==ch) & (st>spontStart) & (st<spontEnd))
      dst_passive = np.diff(st[st_idxs],axis=0)
      hist, _ = np.histogram(dst_passive, logbins)
      # dont divide by zero
      if np.any(hist):
        # normalize the ISI distribution
        hist = hist / np.sum(hist)
        x = channels['x'][ch]
        y = channels['y'][ch]
        z = channels['z'][ch]
        mlapdv = atlas.xyz2ccf([x,y,z])

        amps = clusters['metrics']['amp_median'][chaCluDict[ch]]
        
        data = [ch, mlapdv[0], mlapdv[1], mlapdv[2], channels['atlas_id'][ch], len(chaCluDict[ch]), np.min(amps), np.max(amps)]
        for bi,val in enumerate(logbins[1:]):
          data.append(hist[bi])
        df.loc[i] = data
    # write the dataframe for this EID to disk
    df.to_csv('C:\\proj\\VBL\\nptraj-ephys-server\\pipeline\\isi_amp_data\\'+pid+'_isi_amp.csv')