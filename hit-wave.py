import seaborn as ses
import matplotlib.pyplot as plt
import numpy as np


data =np.random.rand(10,12)
ses.heatmap(data, cmap='Reds')
plt.show()