import unittest

from graph import DCRGraph,DCRChoreography, DCRProjection
from activity import DCRActivity

class TestJolieGenAux(unittest.TestCase):

    def setUp(self):
        # Make a dummy projection.
        self.projection = DCRProjection.from_data("a", dict(), set(), set(), set(), set(), set(),set(),set(),collapse = False)

    def test_gen_port(self):
        port = self.projection.gen_port(True, "From","To")
        ret  = "\tinputPort inFromService {\n"
        ret += "\t\tlocation: \"socket://localhost:port_of_outputPort_'outToService'_in_From\"\n"
        ret += "\t\tprotocol: http { format = \"json\"}\n"
        ret += "\t\tinterfaces: FromToInterface\n"
        ret += "\t}\n\n"
        self.assertEqual(port,ret)

    def test_gen_service_filename_no_file_extension(self):
        service_filename = self.projection.gen_service_filename("Actor",False)
        self.assertEqual(service_filename,"ActorService")

    def test_gen_service_filename_file_extension(self):
        service_filename = self.projection.gen_service_filename("Actor",True)
        self.assertEqual(service_filename,"output/ActorService.ol")

    def test_gen_interface_filename_no_file_extension(self):
        interface_filename = self.projection.gen_interface_filename("Actor",False)
        self.assertEqual(interface_filename,"ActorInterfaces")

    def test_gen_interface_filename_file_extension(self):
        interface_filename = self.projection.gen_interface_filename("Actor",True)
        print()
        self.assertEqual(interface_filename,"output/ActorInterfaces.iol")

    def test_gen_interface_filename(self):
        interface_name = self.projection.gen_interface_name("From","To")
        self.assertEqual(interface_name,"FromToInterface")

    def test_convert_datatype_text(self):
        e = DCRActivity("id","name")
        e.set_datatype("text")
        converted_type = self.projection.convert_datatype(e)
        self.assertEqual(converted_type,"string")

    def test_convert_datatype_bool(self):
        e = DCRActivity("id","name")
        e.set_datatype("bool")
        converted_type = self.projection.convert_datatype(e)
        self.assertEqual(converted_type,"bool")

    def test_convert_datatype_float(self):
        e = DCRActivity("id","name")
        e.set_datatype("float")
        converted_type = self.projection.convert_datatype(e)
        self.assertEqual(converted_type,"double")

    def test_convert_datatype_narwhal(self):
        e = DCRActivity("id","name")
        e.set_datatype("narwhal") # Sadly, this datatype is not implemented.
        converted_type = self.projection.convert_datatype(e)
        self.assertEqual(converted_type,"CUSTOM")

    def test_convert_datatype_none(self):
        e = DCRActivity("id","name")
        converted_type = self.projection.convert_datatype(e)
        self.assertEqual(converted_type,"void")

if __name__ == '__main__':
    unittest.main()

    target = __import__("../graph.py")

