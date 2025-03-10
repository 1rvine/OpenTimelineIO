#!/usr/bin/env python
#
# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the OpenTimelineIO project

import opentimelineio as otio
import opentimelineio.test_utils as otio_test_utils

import unittest


class OpenTimeTypeSerializerTest(unittest.TestCase):

    def test_serialize_time(self):
        rt = otio.opentime.RationalTime(15, 24)
        encoded = otio.adapters.otio_json.write_to_string(rt)
        decoded = otio.adapters.otio_json.read_from_string(encoded)
        self.assertEqual(rt, decoded)

        rt_dur = otio.opentime.RationalTime(10, 20)
        tr = otio.opentime.TimeRange(rt, rt_dur)
        encoded = otio.adapters.otio_json.write_to_string(tr)
        decoded = otio.adapters.otio_json.read_from_string(encoded)
        self.assertEqual(tr, decoded)

        tt = otio.opentime.TimeTransform(rt, scale=1.5)
        encoded = otio.adapters.otio_json.write_to_string(tt)
        decoded = otio.adapters.otio_json.read_from_string(encoded)
        self.assertEqual(tt, decoded)


class SerializableObjTest(unittest.TestCase, otio_test_utils.OTIOAssertions):
    def test_cons(self):
        so = otio.core.SerializableObjectWithMetadata()
        so.metadata['foo'] = 'bar'
        self.assertEqual(so.metadata['foo'], 'bar')

    def test_update(self):
        so = otio.core.SerializableObjectWithMetadata()
        so.metadata.update({"foo": "bar"})
        self.assertEqual(so.metadata["foo"], "bar")
        so_2 = otio.core.SerializableObjectWithMetadata()
        so_2.metadata["foo"] = "not bar"
        so.metadata.update(so_2.metadata)
        self.assertEqual(so.metadata["foo"], "not bar")

    def test_copy_lib(self):
        so = otio.core.SerializableObjectWithMetadata()
        so.metadata["meta_data"] = {"foo": "bar"}

        import copy

        # shallow copy is an error
        with self.assertRaises(ValueError):
            so_cp = copy.copy(so)

        # deep copy
        so_cp = copy.deepcopy(so)
        self.assertIsOTIOEquivalentTo(so, so_cp)

        so_cp.metadata["foo"] = "bar"
        self.assertNotEqual(so, so_cp)

    def test_copy_subclass(self):
        @otio.core.register_type
        class Foo(otio.core.SerializableObjectWithMetadata):
            _serializable_label = "Foof.1"

        foo = Foo()
        foo.metadata["meta_data"] = {"foo": "bar"}

        import copy

        with self.assertRaises(ValueError):
            foo_copy = copy.copy(foo)

        foo_copy = copy.deepcopy(foo)

        self.assertEqual(Foo, type(foo_copy))

    def test_schema_versioning(self):
        @otio.core.register_type
        class FakeThing(otio.core.SerializableObject):
            _serializable_label = "Stuff.1"
            foo_two = otio.core.serializable_field("foo_2", doc="test")
        ft = FakeThing()

        self.assertEqual(ft.schema_name(), "Stuff")
        self.assertEqual(ft.schema_version(), 1)

        with self.assertRaises(otio.exceptions.UnsupportedSchemaError):
            otio.core.instance_from_schema(
                "Stuff",
                2,
                {"foo": "bar"}
            )

        ft = otio.core.instance_from_schema("Stuff", 1, {"foo": "bar"})
        self.assertEqual(ft._dynamic_fields['foo'], "bar")

        @otio.core.register_type
        class FakeThing(otio.core.SerializableObject):
            _serializable_label = "NewStuff.4"
            foo_two = otio.core.serializable_field("foo_2")

        @otio.core.upgrade_function_for(FakeThing, 2)
        def upgrade_one_to_two(_data_dict):
            return {"foo_2": _data_dict["foo"]}

        @otio.core.upgrade_function_for(FakeThing, 3)
        def upgrade_one_to_two_three(_data_dict):
            return {"foo_3": _data_dict["foo_2"]}

        ft = otio.core.instance_from_schema("NewStuff", 1, {"foo": "bar"})
        self.assertEqual(ft._dynamic_fields['foo_3'], "bar")

        ft = otio.core.instance_from_schema("NewStuff", 3, {"foo_2": "bar"})
        self.assertEqual(ft._dynamic_fields['foo_3'], "bar")

        ft = otio.core.instance_from_schema("NewStuff", 4, {"foo_3": "bar"})
        self.assertEqual(ft._dynamic_fields['foo_3'], "bar")

    def test_equality(self):
        o1 = otio.core.SerializableObject()
        o2 = otio.core.SerializableObject()
        self.assertTrue(o1 is not o2)
        self.assertTrue(o1.is_equivalent_to(o2))
        self.assertIsOTIOEquivalentTo(o1, o2)

    def test_equivalence_symmetry(self):
        def test_equivalence(A, B, msg):
            self.assertTrue(A.is_equivalent_to(B), "{}: A ~= B".format(msg))
            self.assertTrue(B.is_equivalent_to(A), "{}: B ~= A".format(msg))

        def test_difference(A, B, msg):
            self.assertFalse(A.is_equivalent_to(B), "{}: A ~= B".format(msg))
            self.assertFalse(B.is_equivalent_to(A), "{}: B ~= A".format(msg))

        A = otio.core.Composable()
        B = otio.core.Composable()
        test_equivalence(A, B, "blank objects")

        A.metadata["key"] = {"a": 0}
        test_difference(A, B, "A has different metadata")

        B.metadata["key"] = {"a": 0}
        test_equivalence(A, B, "add metadata to B")

        A.metadata["key"]["sub-key"] = 1
        test_difference(A, B, "Add dict within A with specific metadata")

    def test_truthiness(self):
        o = otio.core.SerializableObject()
        self.assertTrue(o)

    def test_instancing_without_instancing_support(self):
        o = otio.core.SerializableObjectWithMetadata()
        c = otio.core.SerializableObjectWithMetadata()
        o.metadata["child1"] = c
        o.metadata["child2"] = c
        self.assertTrue(o.metadata["child1"] is o.metadata["child2"])

        oCopy = o.clone()
        # Note: If we ever enable INSTANCING_SUPPORT in the C++ code,
        # then this will (and should) fail
        self.assertTrue(oCopy.metadata["child1"] is not oCopy.metadata["child2"])

    def test_cycle_detection(self):
        o = otio.core.SerializableObjectWithMetadata()
        o.metadata["myself"] = o

        # Note: If we ever enable INSTANCING_SUPPORT in the C++ code,
        # then modify the code below to be:
        #   oCopy = o.clone()
        #   self.assertTrue(oCopy is oCopy.metadata["myself"])
        with self.assertRaises(ValueError):
            o.clone()


if __name__ == '__main__':
    unittest.main()
