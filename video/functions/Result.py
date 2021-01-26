class Result:
    def __init__(self, image_name, results_list):
        self.image_name = image_name
        self.results_list = results_list

    def __str__(self):
        return f'Result(image_name = {self.image_name}, results_list = {self.results_list})'

    def __repr__(self):
        return f'Result(image_name = {self.image_name}, results_list = {self.results_list})'