from getozone import *
from getpm import *
from getvoc import *
import shutil

path = 'whyisthishappeningtomedata.txt'

#try:
#    #shutil copy
#    file = open('/media/pi/ClickUSB/' + path, 'x')
#    file.write('ok so here we paste-a the date-a')
#    file.flush()
#    file.close()
#except:
#    for i in range(1, 11):
#        try:
#            file = open('/media/pi/ClickUSB' + str(i) + '/' + path, 'x')
#            file.write('ok so here we paste-a the date-a')
#            file.flush()
#            file.close()
#            break
#        except PermissionError:
#            pass
        
file = open('/media/pi/ClickUSB3/cmon.txt', 'x')
file.write('afbfwfba14')
file.flush()
file.close()
shutil.copy('/media/pi/ClickUSB3/cmon.txt', '/media/pi/ClickUSB3/wedidit.txt')