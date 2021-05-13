import ftplib
import os
import yaml

yaml_file = open("conf/conf.yml", 'r')
yaml_content = yaml.safe_load(yaml_file)


LOCAL_FOLDER = yaml_content.get("camera").get("local_folder")
REMOTE_FOLDER = yaml_content.get("ftp").get("remote_folder")
FTP_HOST = yaml_content.get("ftp").get("host")
FTP_USER = yaml_content.get("ftp").get("user")
FTP_PASSWORD = yaml_content.get("ftp").get("password")


class FTP:

    def send_file(filename):
        try:
            with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD) as session:
                local_file_path = os.path.join(LOCAL_FOLDER, filename)
                remote_file_path = os.path.join(REMOTE_FOLDER, filename)
                file = open(local_file_path, 'rb')
                session.storbinary('STOR {}'.format(remote_file_path), file)
                file.close()
        except Exception as e:
            print("ERRORW WITH FTP {}".format(e))
