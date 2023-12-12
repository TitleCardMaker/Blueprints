import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

df = pd.DataFrame({
    'Creator': ['CollinHeist', 'flowcool', 'rtgurley'],
    'Blueprints': [136, 32, 13],
})

sns.set_style('whitegrid')

plt.pie(df['Blueprints'], labels=df['Creator'])
plt.show()