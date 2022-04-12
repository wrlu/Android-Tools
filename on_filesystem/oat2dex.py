import lief
import sys

odex_file = sys.argv[1]
vdex_file = sys.argv[2]
oat = lief.OAT.parse(odex_file, vdex_file)
i = 1
for dex_file in oat.dex_files:
    if i == 1:
        dex_file.save('classes.dex')
    else:
        dex_file.save('classes' + str(i) + '.dex')
    i = i + 1
print(str(i) + ' dex files saved.')