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

# Get all eid + probe combinations with timing info, wheel info, spikes, clusters, and channels.
eid_info_map = np.load("C:\\proj\\IBL\\filter_eids\\brainwide_eid_info_map.npy", allow_pickle=True).item()

good_eids = {}
for eid in eid_info_map:
  eid_info = eid_info_map[eid]

  if eid_info["timing_info"] and eid_info["wheel_info"]:
    good_probes = []
    for probe in ['probe00', 'probe01']:
      probe_info = eid_info[probe]
      if probe_info["spikes"] and probe_info["clusters"] and probe_info["channels"]:
        good_probes.append(probe)
    if len(good_probes) > 0:
      good_eids[eid] = good_probes
      
eids = list(good_eids.keys())

# For testing
# eids = [eids[0]]

# Setup the log spacing we'll use to save the ISI distribution
logbins = np.logspace(np.log10(0.001),np.log10(10),10)
logbins = np.insert(logbins,0,0)

# Now run through every *channel* in the data, saving the spike distribution and 


uuid_2_index_fp = 'C:\\proj\\IBL\\cluster_pipelines\\data\\uuid_index.pkl'
with open(uuid_2_index_fp, 'rb') as fp:
  uuid_index = pickle.load(fp)

for eid in eids:
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
    df.to_csv('C:\\proj\\IBL\\cluster_pipelines\\data\\isi_amp_data\\'+pid+'_isi_amp.csv')