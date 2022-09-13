class Rotor:
    def __init__(self, rotor_points, rotor_edge):
        self.suction_points = rotor_points[0]
        self.pressure_points = rotor_points[1]
        self.leading_edge = rotor_edge[0]
        self.trailing_edge = rotor_edge[1]