class Satellite:
    def __init__(self, name, data_path) -> None:
        self.name = name
        self.data_path = data_path

    def __repr__(self) -> str:
        return f"Satellite: {self.name}, data path: {self.data_path}"


class SatelliteCollection:
    CHAMP = Satellite("CHAMP", "/version_02/CHAMP_data")
    GRACE_A_and_B = Satellite("GRACE", "/version_02/GRACE_data")
    GRACE_C = Satellite("GRACE", "/version_02/GRACE-FO_data")
    SWARM = Satellite("SWARM", "/version_01/Swarm_data")
    GOCE = Satellite("GOCE", "/version_01/GOCE_data")

    @classmethod
    def get_all_satellites(cls):
        return [cls.CHAMP, cls.GRACE_A_and_B, cls.GRACE_C, cls.SWARM, cls.GOCE]