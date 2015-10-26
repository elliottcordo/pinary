#!/usr/bin/env python

import RPi.GPIO as GPIO
import picamera
from time import sleep
import os, sys
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
import ConfigParser


class rpi_nary():
    """

    """
    def __init__(self):
        os.chdir(os.path.dirname(sys.argv[0]))
        config = ConfigParser.ConfigParser()
        config.read('conf.cfg')

        self.from_email = config.get('email','from_email')
        self.to_email = config.get('email','to_email')
        self.password = config.get('email','password')
        self.recording_length = config.get('general','recording_length')
        self.wait_time = config.get('general','wait_time')


        self.camera = picamera.PiCamera()

        # setup board and camera
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(7,GPIO.OUT)
        GPIO.setup(11,GPIO.IN)


    def send_gmail (self, from_address, to_address, subject, message, attachment, attachment_name, password):
        msg = MIMEMultipart()

        msg['From'] = from_address
        msg['To'] = to_address
        msg['Subject'] = subject

        body = message

        msg.attach(MIMEText(body, 'plain'))

        filename = attachment_name
        attach = open(attachment, "rb")

        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attach).read())

        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

        msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_address, password)
        text = msg.as_string()
        server.sendmail(from_address, to_address, text)
        server.quit()


    def record_video(self, file_name):
        self.camera.start_recording(file_name + '.h264')
        self.camera.wait_recording(self.recording_length)
        self.camera.stop_recording()
        out_file = file_name + '.mp4'

        try:
            os.remove(out_file )
        except: pass

        os.system('MP4Box -fps 30 -add ' + file_name + '.h264 ' + out_file)
        return out_file

    def take_picture(self, file_name):
        out_file = file_name + '.jpg'
        self.camera.capture(out_file)
        return out_file

    def startup(self):
        out_file = self.take_picture('startup')
        self.send_gmail(from_address=self.from_email, to_address=self.to_email, subject='security startup',
                        message='startup', attachment=out_file, attachment_name=out_file, password=self.password )

    def run(self):
        """
        main entry point
        :return:
        """
        # take picture on startup
        self.startup()

        # main loop
        n = 1
        while True:

            if GPIO.input(11) == 1:
                # turn on LED
                GPIO.output(7, True)

                # take picture and email
                file_name = 'intruder' + str(n)
                out_file = self.record_video(file_name)

                n += 1

                self.send_gmail(from_address=self.from_email, to_address=self.to_email, subject='intruder',
                                message='intruder', attachment=out_file, attachment_name=out_file, password=self.password )

                # turn off LED and wait
                GPIO.output(7, False)
                sleep(self.wait_time)

                # only save last 50 pics
                if n > 50:
                    n = 1

if __name__ == "__main__":
    rpi = rpi_nary()
    rpi.run()
