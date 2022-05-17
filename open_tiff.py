import large_image


imagePath = r"F:\projects\django-project\data\montage.tiff"
source = large_image.open(imagePath)
band_infos = source.getBandInformation()
print(band_infos)


