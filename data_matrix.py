
"""
data_matrix.py

Author: Eric
github: ZwodahS

data_matrix is a simple modules that helps you count on a N-dimension matrix.

terminology:

    data: a single entry in the matrix
    tag: a tag is a single label given to a data

    tags is like the row/column in a 2dimension matrix

"""
import json
INT="INT"
STRING="STR"
BOOL="BOOL"

RANGE="RANGE" # only for int
DISTINCT="DISTINCT"

__COUNT__ = "__COUNT__"

class DataMatrix(object):

    def __init__(self, tags):
        """
        tags : defines what each data point are and their valid values
        {
            "<name>" : { "type": (INT | STR), "range": (RANGE | DISTINCT) }
        }
        """
        self._init_tags(tags)

    def _init_tags(self, tags):
        for name, tag in tags.items():
            self._assert_type(tag.get("type"))
            self._assert_range(tag.get("range"), tag.get("type"))

        self.tags = tags
        self._datas = []
        self._matrix = {}
        self._tag_order = [ tag_name for tag_name in tags ]
        self._tag_values = { tag_name : set() for tag_name in tags }

    def save(self, filename):
        data = {
            "tags" : self.tags,
            "_datas": self._datas,
            "_matrix": self._matrix,
            "_tag_order": self._tag_order,
            "_tag_values": { k: list(l) for k, l in self._tag_values.items() },
        }
        with open(filename, "w") as f:
            f.write(json.dumps(data, indent=4))
            # f.write(json.dumps(data, indent=4, separators=(",", ": ")))

    def load(self, filename):
        with open(filename) as f:
            data = json.loads(f.read())

        self.tags = data.get("tags")
        self._datas = data.get("_datas")
        self._tag_order = data.get("_tag_order")
        self._tag_values = { k: set(l) for k, l in data.get("_tag_values").items() }
        _matrix = data.get("_matrix")
        self._set_matrix(_matrix)

    def _set_matrix(self, matrix):
        tags = [ self.tags.get(tag_name) for tag_name in self._tag_order ]
        self._matrix = self._construct_matrix(tags, matrix)

    def _construct_matrix(self, tags, matrix):
        if len(tags) == 0:
            return matrix
        if tags[0].get("type") == INT:
            return { int(key) : self._construct_matrix(tags[1:], value) for key, value in matrix.items() }
        else:
            return { key : self._construct_matrix(tags[1:], value) for key, value in matrix.items() }

    def _assert_type(self, data_type):
        if data_type not in (INT, STRING, BOOL):
            raise Exception("Invalid data type {0}".format(data_type))

    def _assert_range(self, data_range, data_type):
        valid = tuple()
        if data_type == INT:
            valid = (RANGE, DISTINCT)
        elif data_type == STRING:
            valid = (DISTINCT, )
        elif data_type == BOOL:
            valid = (DISTINCT, )
        if data_range not in valid:
            raise Exception("Invalid tag range '{0}' for type '{1}'".format(data_range, data_type))

    def _clean_value_for_tag(self, tag_name, value):
        tag = self.tags.get(tag_name)
        if tag is None:
            raise Exception("Invalid name for tag {0}".format(tag_name))
        if tag["type"] == INT:
            try:
                value = int(value)
            except Exception as e:
                raise Exception("Invalid value for tag {0} : {1}".format(tag_name, value))
        elif tag["type"] == STRING:
            if not isinstance(value, str):
                raise Exception("Invalid value for tag {0} : {1}".format(tag_name, value))
        elif tag["type"] == BOOL:
            try:
                value = bool(value)
            except Exception as e:
                raise Exception("Invalid value for tag {0} : {1}".format(tag_name, value))
        return value

    def set_data(self, data, **tags):
        """If data is none, only increase count
        """
        if data is not None:
            self._datas.append((data, tags))

        for tag_name in tags:
            if tag_name not in self.tags:
                raise Exception("tag {0} is not in defined tag".format(tag_name))
        if len(tags) != len(self.tags):
            raise Exception("All data must be tag to all defined tags")

        ordered = [ self._clean_value_for_tag(tag_name, tags.get(tag_name)) for tag_name in self._tag_order ]
        current = self._matrix
        for ordered_value in ordered:
            if ordered_value not in current:
                current[ordered_value] = {}
            current = current[ordered_value]
        if __COUNT__ not in current:
            current[__COUNT__] = 0
        current[__COUNT__] += 1

        for tag_name, tag_value in tags.items():
            if tag_name in self._tag_values:
                self._tag_values[tag_name].add(tag_value)


    def get_count(self, **tags):
        tag_query = []
        for tag_name in self._tag_order:
            if tag_name in tags:
                tag_query.append(tags.get(tag_name))
            else:
                tag_query.append(None)

        return self._get_count(self._matrix, tag_query)

    def _get_count(self, current_data, tags_list):
        if current_data is None:
            return 0

        if len(tags_list) == 0:
            return current_data.get(__COUNT__)

        current_tag = tags_list[0]
        if current_tag is None:
            counts = [ self._get_count(d, tags_list[1:]) for _, d in current_data.items() ]
            return sum(counts)
        elif isinstance(current_tag, (list, tuple)):
            return sum([self._get_count(current_data.get(tag), tags_list[1:]) for tag in current_tag])
        else:
            d = current_data.get(current_tag)
            return self._get_count(d, tags_list[1:])

    def get_range(self, tag_name, raise_error=True):
        tag = self.tags.get(tag_name)
        if tag is None:
            if raise_error:
                raise Exception("tag {0} not found".format(field_name))
            else:
                return None

        if tag.get("range") == DISTINCT:
            return list(self._tag_values[tag_name])
        else:
            values = list(self._tag_values[tag_name])
            values.sort()
            min_value = values[0]
            max_value = values[-1]
            return list(range(min_value, max_value+1))

    def generate_table(self, row_field, column_field, include_header=True, include_row_total=True,
            include_column_total=True, **filters):
        """
        row_field/column_field can be a tuple or a single string
        if is string, the range will be iterated based on what is entered
        if it is tuple, then the second value must be a list or tuple and those value will be used instead

        """
        row_values = self.get_range(row_field) if isinstance(row_field, str) else list(row_field[1])
        column_values = self.get_range(column_field) if isinstance(column_field, str) else list(column_field[1])
        row_field = row_field if isinstance(row_field, str) else row_field[0]
        column_field = column_field if isinstance(column_field, str) else column_field[0]

        output = []

        if include_header:
            header = [None] + column_values
            if include_column_total:
                header.append("total")
            output.append(header)

        for row_value in row_values:
            row_data = []
            if include_header:
                row_data.append(row_value)
            for column_value in column_values:
                new_filters = {}
                new_filters.update(filters)
                new_filters[row_field] = row_value
                new_filters[column_field] = column_value
                row_data.append(self.get_count(**new_filters))

            if include_column_total:
                new_filters = {}
                new_filters.update(filters)
                new_filters[row_field] = row_value
                row_data.append(self.get_count(**new_filters))

            output.append(row_data)

        if include_row_total:
            total_row = []
            if include_header:
                total_row.append("total")
            for column_value in column_values:
                new_filters = {}
                new_filters.update(filters)
                new_filters[column_field] = column_value
                total_row.append(self.get_count(**new_filters))

            if include_column_total:
                total_row.append(self.get_count(**filters))
            output.append(total_row)

        return output


if __name__ == "__main__":

    matrix = DataMatrix(tags={
                "school":  { "type": STRING, "range": DISTINCT},
                "age": {"type": INT, "range": RANGE},
                "gender": {"type": STRING, "range": DISTINCT},
                "town": {"type": STRING, "range": DISTINCT},
                "vegetarian": {"type": BOOL, "range": DISTINCT},
            })

    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_A", vegetarian=True)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="M", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=7, gender="F", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=7, gender="F", town="Town_A", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_B", age=8, gender="F", town="Town_B", vegetarian=False)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_B", vegetarian=True)
    matrix.set_data(None, school="School_A", age=8, gender="M", town="Town_B", vegetarian=True)

    assert matrix.get_count(school="School_A") == 51
    assert matrix.get_count(school="School_B") == 48
    assert matrix.get_count(school=("School_B", "School_A")) == 99
    assert matrix.get_count(gender="M") == 45
    assert matrix.get_count(gender="F") == 54
    assert matrix.get_count(age=7) == 48
    assert matrix.get_count(age=8) == 51
    assert matrix.get_count(vegetarian=True) == 51
    assert matrix.get_count(vegetarian=False) == 48
    assert matrix.get_count(town="Town_A") == 42
    assert matrix.get_count(town="Town_B") == 57

    assert matrix.get_count(school="School_A", town="Town_A") == 18
    assert matrix.get_count(school="School_A", town="Town_B") == 33
    assert matrix.get_count(school="School_B", town="Town_A") == 24
    assert matrix.get_count(school="School_B", town="Town_B") == 24

    print(matrix.generate_table(row_field="age", column_field="school"))
    print(matrix.generate_table(row_field="age", column_field=("school", ("School_A",))))
    print(matrix.generate_table(row_field="age", column_field="age"))
