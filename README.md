# DEM to Depthmap

Nice commands:


Translate from .dem or .tif to .png:
```
gdal_translate -ot UInt16 -of PNG 6700_3_10m_z33.dem test.png
```

```

demList = glob.glob("assets/bgo[1-9].tif")
print(demList)

cmd = "gdal_merge.py -ps 10 -10 -o mergedDEM.tif"
subprocess.call(cmd.split()+demList)
cmd = "gdal_merge.py -o mergedDEM.dem"
subprocess.call(cmd.split()+demList)

vrt = gdal.BuildVRT("merged.vrt", demList)
gdal.Translate("assets/mgdDEM2.tif", vrt, xRes = 10, yRes = -10)
vrt = None
```
