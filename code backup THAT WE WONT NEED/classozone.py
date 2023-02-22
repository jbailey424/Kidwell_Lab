import time
import math
import automationhat

class MQ131():
    RL = 10
    RO_CAF = 1 #set RL which doesnt matter and RO_CAF the graph clean air ratio
    
    caltimes = 50 #samples in calibration
    calinterval = 0.1 #time between calibration samples, rn calibration takes 25 seconds TOO LONG!
    readtimes = 5 #samples in reading
    readinterval = 0.005 #time between read samples
    
    gasozone = 0
    #etc, set variables for each gas youre sensing
    
    def __init__(self):
        self.Ro = 0
        self.adc = automationhat.analog.three #which pin in the hat are we plugged into!
        
        self.ozonecurve = [1.69897,0.301,0.47712] #[x, y, slope] from a known point on the gases graph and the slope between two points
        
        automationhat.light.power.toggle()        
        print("Calibrating MQ131...")
        self.Ro = self.MQcalibration()
        print("MQ131 calibration is done :) \n")
        automationhat.light.power.toggle() 

    def MQcalibration(self):
        val = 0.0
        for i in range(self.caltimes):
            val += self.MQresistancecalc(self.adc.read()) #self.adc.read reads the inputted automationhat analog channel
            time.sleep(self.calinterval)   
        val = val/self.caltimes # calculate the average value
        val = val/self.RO_CAF # divided by RO_CLEAN_AIR_FACTOR yields the Ro according to the chart in the datasheet 
        return val

    def MQresistancecalc(self, raw_adc): #takes the input from adc.read and converts it to a resistance value using the given load resistance
        return float(self.RL*(25.85-raw_adc)/float(raw_adc));
    
    def MQread(self): #takes the average signal over a short interval and converts it to resistance
        rs = 0.0
        for i in range(self.readtimes):
            rs += self.MQresistancecalc(self.adc.read())
            time.sleep(self.readinterval)
        rs = rs/self.readtimes
        return rs
    
    def MQgetconcentration(self, rs_ro_ratio, gas_id): #given an id for the gas and the current reading, calculate concentration. GAS READINGS ARE NOT INDEPENDENT, THEY ALL USE THE SAME INPUT ON A DIFFERENT CURVE
        if (gas_id == self.gasozone): #so the same signal correlates to conc1 of gas1 and conc2 of gas2, the gas youre reading DOESNT have both, you have either or a mix.
            return self.MQgetpercentage(rs_ro_ratio, self.ozonecurve)
        return 0
    
    def MQgetpercentage(self, rs_ro_ratio, pcurve): #uses the inputted point and slope to approximate where your read rs/r0 falls on the curve relative to ppm
        return (math.pow(10,( ((math.log(rs_ro_ratio, 10)-pcurve[1])/ pcurve[2]) + pcurve[0])))
    
    def MQpercentage(self): #this one just compiles all the above functions to read and then output a gas concentration.
        val = {} #this is the function you call, the rest just help with this
        read = self.MQread()
        val["gasozone"]  = self.MQgetconcentration(read/self.Ro, self.gasozone)
        return val
