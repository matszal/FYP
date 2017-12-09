import com.pi4j.io.gpio.*;
import com.pi4j.io.gpio.event.GpioPinDigitalStateChangeEvent;
import com.pi4j.io.gpio.event.GpioPinListenerDigital;
import com.pi4j.wiringpi.GpioUtil;

public class PirMotionDetection{
    public void detectMotion()    {
        System.out.println("Starting Motion Sensor Test");
        System.out.println("Pir motion sensor is ready and waiting for movement...");

        //This is required to enable non privileged access to avoid applying sudo to run pi4j programs
        GpioUtil.enableNonPrivilegedAccess();

        //Create gpio controller forPIR Motion Sensor listening on the pin gpio_07
        final GpioController gpioPIRMotionSensor = GpioFactory.getInstance();
        final GpioPinDigitalInput pirMotionSensor = gpioPIRMotionSensor.provisionDigitalInputPin(RaspiPin.GPIO_07,
                PinPullResistance.PULL_DOWN);

        //Create and register gpio pin listener on PIRMotion Sensor GPIO Input instance
        pirMotionSensor.addListener(new GpioPinListenerDigital()
        {
            @Override
            public void handleGpioPinDigitalStateChangeEvent(GpioPinDigitalStateChangeEvent event)
            {
                //if the event state is HIGH then print intruder detected
                if (event.getState().isHigh()){
                    System.out.println("Intruder detected");
                }
                else{
                    System.out.println("No movement...");
                }
            }
        });

        try{
            while(true){
                //Keep program running until terminated by user ctrl-c
            }
        }
        catch (Exception e){
            e.printStackTrace();
        }
    }

}
