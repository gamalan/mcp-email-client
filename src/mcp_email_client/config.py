import json, os

class MailConfig:
    def __init__(self, _name: str, inbound_host: str, inbound_port: int, inbound_user: str, inbound_password: str, inbound_ssl: str="SSL/TLS", is_outbound_equal: bool=True, outbound_host: str="", outbound_port: int=0, outbound_user: str="", outbound_password: str="", outbound_ssl: str=""):
        self._name = _name
        self.inbound_host = inbound_host
        self.inbound_port = inbound_port
        self.inbound_user = inbound_user
        self.inbound_password = inbound_password
        self.inbound_ssl = inbound_ssl
        self.is_outbound_equal = is_outbound_equal
        if self.is_outbound_equal:
            self.outbound_host = self.inbound_host
            self.outbound_port = self.inbound_port
            self.outbound_user = self.inbound_user
            self.outbound_password = self.inbound_password
            self.outbound_ssl = self.inbound_ssl
        else:
            self.outbound_host = outbound_host
            self.outbound_port = outbound_port
            self.outbound_user = outbound_user
            self.outbound_password = outbound_password
            self.outbound_ssl = outbound_ssl
        self.config_file = os.path.join(os.path.dirname(__file__),"config", self.name +'.json')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        self.config_file = os.path.join(os.path.dirname(__file__),"config", value +'.json')

    def save_entry(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.__dict__, f)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save_entry()

    def __str__(self):
        return f"MailConfig(name={self._name}, inbound_host={self.inbound_host}, inbound_port={self.inbound_port}, inbound_user={self.inbound_user}, inbound_password={self.inbound_password}, inbound_ssl={self.inbound_ssl}, outbound_host={self.outbound_host}, outbound_port={self.outbound_port}, outbound_user={self.outbound_user}, outbound_password={self.outbound_password}, outbound_ssl={self.outbound_ssl})"

    @staticmethod
    def load_entry(name):
        with open(os.path.join(os.path.dirname(__file__),"config", name + '.json'), 'r') as f:
            data = json.load(f)
            del data['config_file']
            return MailConfig(**data)

    @staticmethod
    def delete_entry(name:str):
        return os.remove(os.path.join(os.path.dirname(__file__),"config", name + '.json'))

    @staticmethod
    def load_all():
        configs = []
        for file in os.listdir(os.path.join(os.path.dirname(__file__),"config")):
            if file.endswith('.json'):
                with open(os.path.join(os.path.dirname(__file__),"config", file), 'r') as f:
                    data = json.load(f)
                    del data['config_file']
                    configs.append(MailConfig(**data))
        return configs


#mail_config = MailConfig("default", "smtp.example.com", 587, "user@example.com", "password", "SSL/TLS", False, "smtp.example.com", 587, "user@example.com", "password", "SSL/TLS")
#mail_config.save_entry()
#mail_config.name = "new_name"
#mail_config.save_entry()
#MailConfig.delete_entry("default")
#mail_config = MailConfig.load_entry("new_name")
#print(mail_config)
#mail_config.update(outbound_host="smtp.example.com", outbound_port=465, outbound_user="user@example.com", outbound_password="password", outbound_ssl="SSL/TLS")
#print(mail_config)
