class Student:
    def __init__(self, id,name, age, mobile,school_id, total_score):
        self.id = id
        self.name = name
        self.age = age
        self.mobile = mobile
        self.total_score = total_score
        self.school_id=school_id

    def __str__(self):
        return (f"ID: {self.id}, Age: {self.age},Name: {self.name}, School: {self.school_id}, "
                f"Position: {self.mobile}, Score: {self.total_score}")

    def to_dict(self):
        return {
            "id": self.id,
            "age": self.age,
            "name": self.name,
            "mobile": self.mobile,
            "school_id": self.school_id,
            "total_score": self.total_score,
        }
