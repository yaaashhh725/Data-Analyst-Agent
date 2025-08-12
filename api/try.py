import pandas as pd
import numpy as np

data = {
    "A": np.random.rand(100),
    "B": np.random.rand(100),
    "C": np.random.rand(100)
}

df = pd.DataFrame(data) 
print(df)