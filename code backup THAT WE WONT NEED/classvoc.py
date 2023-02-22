import time
import math
import automationhat

class MQ138():
    RL = 17.5
    RO_CAF = 3.7 #set MCP pin that you dont use, RL which doesnt matter, and RO_CAF the graph clean air ratio
    
    caltimes = 50 #samples in calibration
    calinterval = 0.1 #time between calibration samples, rn calibration takes 25 seconds TOO LONG!
    readtimes = 5 #samples in reading
    readinterval = 0.005 #time between read samples
    
    gas_methanol = 0
    gas_formaldehyde = 1
    gas_toluene = 2
    #etc, set variables for each gas youre sensing
    
    def __init__(self):
        self.Ro = 0
        self.adc = automationhat.analog.two #which pin in the hat are we plugged into!
        
        self.methanolcurve = [2.301,-0.0969,-0.3641] #[x, y, slope] from a known point on the gases graph and the slope between two points
        self.formaldehydecurve = [2,0,-0.4149]
        self.toluenecurve = [2,-0.0969,-0.3010]
        
        automationhat.light.power.toggle()        
        print("Calibrating VOC...")
        self.Ro = self.MQcalibration()
        print("MQ138 Calibration is done...\n")
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
        if (gas_id == self.gas_methanol):
            #(rs_ro_ratio)#so the same signal correlates to conc1 of gas1 and conc2 of gas2, the gas youre reading DOESNT have both, you have either or a mix.
            return self.MQgetpercentage(rs_ro_ratio, self.methanolcurve)
        elif (gas_id == self.gas_formaldehyde):
            return self.MQgetpercentage(rs_ro_ratio, self.formaldehydecurve)
        elif (gas_id == self.gas_toluene):
            return self.MQgetpercentage(rs_ro_ratio, self.toluenecurve)
        return 0
    
    def MQgetpercentage(self, rs_ro_ratio, pcurve): #uses the inputted point and slope to approximate where your read rs/r0 falls on the curve relative to ppm
        return (math.pow(10,( ((math.log(rs_ro_ratio, 10)-pcurve[1])/ pcurve[2]) + pcurve[0])))
    
    def MQpercentage(self): #this one just compiles all the above functions to read and then output a gas concentration.
        val = {} #this is the function you call, the rest just help with this
        read = self.MQread()
        #print(read/self.Ro, 'heres ratio')
        val["methanol"]  = self.MQgetconcentration(read/self.Ro, self.gas_methanol)
        val["formaldehyde"]       = self.MQgetconcentration(read/self.Ro, self.gas_formaldehyde)
        val["toluene"]    = self.MQgetconcentration(read/self.Ro, self.gas_toluene)
        return val
