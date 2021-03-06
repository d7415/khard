"""Tests for the carddav module."""

import datetime
import unittest
from unittest import mock

import vobject

from khard import carddav_object


def _create_test_vcard(**kwargs):
    """Create a simple vcard for tests."""
    vcard = vobject.vCard()
    if 'fn' not in kwargs:
        kwargs['fn'] = 'Test vCard'
    if 'version' not in kwargs:
        kwargs['version'] = '3.0'
    for key, value in kwargs.items():
        vcard.add(key.upper()).value = value
    return vcard


class VcardWrapperInit(unittest.TestCase):

    def test_stores_vcard_object_unmodified(self):
        vcard = _create_test_vcard()
        expected = vcard.serialize()
        wrapper = carddav_object.VCardWrapper(vcard)
        # assert that it is the same object
        self.assertIs(wrapper.vcard, vcard)
        # assert that it (the serialization) was not changed
        self.assertEqual(wrapper.vcard.serialize(), expected)

    def test_warns_about_unsupported_version(self):
        vcard = _create_test_vcard(version="something unsupported")
        with self.assertLogs(level="WARNING"):
            carddav_object.VCardWrapper(vcard)

    def test_warns_about_missing_version_and_sets_it(self):
        vcard = _create_test_vcard()
        vcard.remove(vcard.version)
        with self.assertLogs(level="WARNING"):
            wrapper = carddav_object.VCardWrapper(vcard)
        self.assertEqual(wrapper.version, "3.0")


class DeleteVcardObject(unittest.TestCase):

    def test_deletes_fields_given_in_upper_case(self):
        vcard = _create_test_vcard()
        expected = vcard.serialize()
        vcard.add('FOO').value = 'bar'
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._delete_vcard_object('FOO')
        self.assertEqual(wrapper.vcard.serialize(), expected)

    def test_deletes_all_field_occurences(self):
        vcard = _create_test_vcard()
        expected = vcard.serialize()
        vcard.add('FOO').value = 'bar'
        vcard.add('FOO').value = 'baz'
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._delete_vcard_object('FOO')
        self.assertEqual(wrapper.vcard.serialize(), expected)

    def test_deletes_grouped_ablabel_fields(self):
        vcard = _create_test_vcard()
        expected = vcard.serialize()
        foo = vcard.add('FOO')
        foo.value = 'bar'
        foo.group = 'group1'
        label = vcard.add('X-ABLABEL')
        label.value = 'test label'
        label.group = foo.group
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._delete_vcard_object('FOO')
        self.assertEqual(wrapper.vcard.serialize(), expected)

    def test_keeps_other_fields(self):
        vcard = _create_test_vcard(foo='bar')
        expected = vcard.serialize()
        vcard.add('BAR').value = 'baz'
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._delete_vcard_object('BAR')
        self.assertEqual(wrapper.vcard.serialize(), expected)

    def test_does_not_fail_on_non_existing_field_name(self):
        vcard = _create_test_vcard(foo='bar')
        expected = vcard.serialize()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._delete_vcard_object('BAR')
        self.assertEqual(wrapper.vcard.serialize(), expected)


class BirthdayLikeAttributes(unittest.TestCase):

    def test_birthday_supports_setting_date_objects(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        date = datetime.datetime(2018, 2, 1)
        wrapper.birthday = date
        wrapper.vcard.validate()
        self.assertEqual(wrapper.birthday, date)

    def test_birthday_supports_setting_datetime_objects(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        date = datetime.datetime(2018, 2, 1, 19, 29, 31)
        wrapper.birthday = date
        wrapper.vcard.validate()
        self.assertEqual(wrapper.birthday, date)

    def test_birthday_supports_setting_text_values_for_v4(self):
        vcard = _create_test_vcard(version="4.0")
        wrapper = carddav_object.VCardWrapper(vcard)
        date = 'some time yesterday'
        wrapper.birthday = date
        wrapper.vcard.validate()
        self.assertEqual(wrapper.birthday, date)

    def test_birthday_does_not_support_setting_text_values_for_v3(self):
        vcard = _create_test_vcard(version="3.0")
        wrapper = carddav_object.VCardWrapper(vcard)
        with self.assertLogs(level='WARNING'):
            wrapper.birthday = 'some time yesterday'
        wrapper.vcard.validate()
        self.assertIsNone(wrapper.birthday)

    def test_anniversary_supports_setting_date_objects(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        date = datetime.datetime(2018, 2, 1)
        wrapper.anniversary = date
        wrapper.vcard.validate()
        self.assertEqual(wrapper.anniversary, date)

    def test_anniversary_supports_setting_datetime_objects(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        date = datetime.datetime(2018, 2, 1, 19, 29, 31)
        wrapper.anniversary = date
        wrapper.vcard.validate()
        self.assertEqual(wrapper.anniversary, date)

    def test_anniversary_supports_setting_text_values_for_v4(self):
        vcard = _create_test_vcard(version="4.0")
        wrapper = carddav_object.VCardWrapper(vcard)
        date = 'some time yesterday'
        wrapper.anniversary = date
        wrapper.vcard.validate()
        self.assertEqual(wrapper.anniversary, date)

    def test_anniversary_does_not_support_setting_text_values_for_v3(self):
        vcard = _create_test_vcard(version="3.0")
        wrapper = carddav_object.VCardWrapper(vcard)
        with self.assertLogs(level='WARNING'):
            wrapper.birthday = 'some time yesterday'
        wrapper.vcard.validate()
        self.assertIsNone(wrapper.anniversary)


class NameAttributes(unittest.TestCase):

    def test_fn_can_be_set_with_a_string(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper.formatted_name = 'foo bar'
        self.assertEqual(vcard.fn.value, 'foo bar')

    def test_only_one_fn_will_be_stored(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper.formatted_name = 'foo bar'
        self.assertEqual(len(vcard.contents['fn']), 1)

    def test_fn_is_returned_as_string(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        self.assertIsInstance(wrapper.formatted_name, str)

    def test_fn_is_used_as_string_representation(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        self.assertEqual(str(wrapper), wrapper.formatted_name)

    def test_name_can_be_set_with_empty_strings(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name('', '', '', '', '')
        self.assertEqual(vcard.serialize(),
                         'BEGIN:VCARD\r\n'
                         'VERSION:3.0\r\n'
                         'FN:Test vCard\r\n'
                         'N:;;;;\r\n'
                         'END:VCARD\r\n')

    def test_name_can_be_set_with_empty_lists(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name([], [], [], [], [])
        self.assertEqual(vcard.serialize(),
                         'BEGIN:VCARD\r\n'
                         'VERSION:3.0\r\n'
                         'FN:Test vCard\r\n'
                         'N:;;;;\r\n'
                         'END:VCARD\r\n')

    def test_name_can_be_set_with_lists_of_empty_strings(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name(['', ''], ['', ''], ['', ''], ['', ''], ['', ''])
        self.assertEqual(vcard.serialize(),
                         'BEGIN:VCARD\r\n'
                         'VERSION:3.0\r\n'
                         'FN:Test vCard\r\n'
                         'N:;;;;\r\n'
                         'END:VCARD\r\n')

    def test_get_first_name_last_name_retunrs_fn_if_no_name_present(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        self.assertEqual(wrapper.get_first_name_last_name(), 'Test vCard')

    def test_get_first_name_last_name_with_simple_name(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name('', 'given', '', 'family', '')
        self.assertEqual(wrapper.get_first_name_last_name(), "given family")

    def test_get_first_name_last_name_with_all_name_fields(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name('prefix', 'given', 'additional', 'family', 'suffix')
        self.assertEqual(wrapper.get_first_name_last_name(),
                         'given additional family')

    def test_get_first_name_last_name_with_complex_name(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name(['prefix1', 'prefix2'], ['given1', 'given2'],
                          ['additional1', 'additional2'],
                          ['family1', 'family2'], ['suffix1', 'suffix2'])
        self.assertEqual(wrapper.get_first_name_last_name(), 'given1 given2 '
                         'additional1 additional2 family1 family2')

    def test_get_last_name_first_name_retunrs_fn_if_no_name_present(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        self.assertEqual(wrapper.get_last_name_first_name(), 'Test vCard')

    def test_get_last_name_first_name_with_simple_name(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name('', 'given', '', 'family', '')
        self.assertEqual(wrapper.get_last_name_first_name(), "family, given")

    def test_get_last_name_first_name_with_all_name_fields(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name('prefix', 'given', 'additional', 'family', 'suffix')
        self.assertEqual(wrapper.get_last_name_first_name(),
                         'family, given additional')

    def test_get_last_name_first_name_with_complex_name(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_name(['prefix1', 'prefix2'], ['given1', 'given2'],
                          ['additional1', 'additional2'],
                          ['family1', 'family2'], ['suffix1', 'suffix2'])
        self.assertEqual(wrapper.get_last_name_first_name(), 'family1 family2,'
                         ' given1 given2 additional1 additional2')


class TypedProperties(unittest.TestCase):

    def test_adding_a_simple_phone_number(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_phone_number('home', '0123456789')
        self.assertDictEqual(wrapper.phone_numbers, {'home': ['0123456789']})

    def test_adding_a_custom_type_phone_number(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_phone_number('custom_type', '0123456789')
        self.assertDictEqual(wrapper.phone_numbers,
                             {'custom_type': ['0123456789']})

    def test_adding_multible_phone_number(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_phone_number('work', '0987654321')
        wrapper._add_phone_number('home', '0123456789')
        wrapper._add_phone_number('home', '0112233445')
        self.assertDictEqual(
            wrapper.phone_numbers,
            # The lists are sorted!
            {'home': ['0112233445', '0123456789'], 'work': ['0987654321']})

    def test_adding_preferred_phone_number(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_phone_number('home', '0123456789')
        wrapper._add_phone_number('pref,home', '0987654321')
        self.assertDictEqual(
            wrapper.phone_numbers, {'home': ['0123456789'],
                                    'home, pref': ['0987654321']})

    def test_adding_a_simple_email(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper.add_email('home', 'foo@bar.net')
        self.assertDictEqual(wrapper.emails, {'home': ['foo@bar.net']})

    def test_adding_a_custom_type_emails(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper.add_email('custom_type', 'foo@bar.net')
        self.assertDictEqual(wrapper.emails,
                             {'custom_type': ['foo@bar.net']})

    def test_adding_multible_emails(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper.add_email('work', 'foo@bar.net')
        wrapper.add_email('home', 'foo@baz.net')
        wrapper.add_email('home', 'baz@baz.net')
        self.assertDictEqual(
            wrapper.emails,
            # The lists are sorted!
            {'home': ['baz@baz.net', 'foo@baz.net'], 'work': ['foo@bar.net']})

    def test_adding_preferred_emails(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper.add_email('home', 'foo@bar.net')
        wrapper.add_email('pref,home', 'foo@baz.net')
        self.assertDictEqual(wrapper.emails, {'home': ['foo@bar.net'],
                                              'home, pref': ['foo@baz.net']})

    def test_adding_a_simple_address(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        components = ('box', 'extended', 'street', 'code', 'city', 'region',
                      'country')
        wrapper._add_post_address('home', *components)
        expected = {item: item for item in components}
        self.assertDictEqual(wrapper.post_addresses, {'home': [expected]})

    def test_adding_a_custom_type_address(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        components = ('box', 'extended', 'street', 'code', 'city', 'region',
                      'country')
        wrapper._add_post_address('custom_type', *components)
        expected = {item: item for item in components}
        self.assertDictEqual(wrapper.post_addresses,
                             {'custom_type': [expected]})

    def test_adding_multible_addresses(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        components = ('box', 'extended', 'street', 'code', 'city', 'region',
                      'country')
        wrapper._add_post_address('work', *['work ' + c for c in components])
        wrapper._add_post_address('home', *['home1 ' + c for c in components])
        wrapper._add_post_address('home', *['home2 ' + c for c in components])
        expected_work = {item: 'work ' + item for item in components}
        expected_home2 = {item: 'home2 ' + item for item in components}
        expected_home1 = {item: 'home1 ' + item for item in components}
        self.assertDictEqual(wrapper.post_addresses,
                             # The lists are sorted!
                             {'home': [expected_home1, expected_home2],
                              'work': [expected_work]})

    def test_adding_preferred_address(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        components = ('box', 'extended', 'street', 'code', 'city', 'region',
                      'country')
        wrapper._add_post_address('home', *['home1 ' + c for c in components])
        wrapper._add_post_address('pref,home',
                                  *['home2 ' + c for c in components])
        expected_work = {item: 'work ' + item for item in components}
        expected_home2 = {item: 'home2 ' + item for item in components}
        expected_home1 = {item: 'home1 ' + item for item in components}
        self.assertDictEqual(
            wrapper.post_addresses, {'home': [expected_home1],
                                     'home, pref': [expected_home2]})


class OtherProperties(unittest.TestCase):

    def test_setting_and_getting_organisations(self):
        # also test that organisations are returned in sorted order
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        org1 = ["Org", "Sub1", "Sub2"]
        org2 = ["Org2", "Sub3"]
        org3 = ["Foo", "Bar", "Baz"]
        wrapper._add_organisation(org1)
        wrapper._add_organisation(org2)
        wrapper._add_organisation(org3)
        self.assertListEqual(wrapper.organisations, [org3, org1, org2])

    def test_setting_and_getting_titles(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_title('Foo')
        wrapper._add_title('Bar')
        self.assertListEqual(wrapper.titles, ['Bar', 'Foo'])

    def test_setting_and_getting_roles(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_role('Foo')
        wrapper._add_role('Bar')
        self.assertListEqual(wrapper.roles, ['Bar', 'Foo'])

    def test_setting_and_getting_nicks(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_nickname('Foo')
        wrapper._add_nickname('Bar')
        self.assertListEqual(wrapper.nicknames, ['Bar', 'Foo'])

    def test_setting_and_getting_notes(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_note('First long note')
        wrapper._add_note('Second long note\nwith newline')
        self.assertListEqual(wrapper.notes, ['First long note',
                             'Second long note\nwith newline'])

    def test_setting_and_getting_webpages(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_webpage('https://github.com/scheibler/khard')
        wrapper._add_webpage('http://example.com')
        self.assertListEqual(wrapper.webpages, ['http://example.com',
                             'https://github.com/scheibler/khard'])

    def test_setting_and_getting_categories(self):
        vcard = _create_test_vcard()
        wrapper = carddav_object.VCardWrapper(vcard)
        wrapper._add_category(["rfc", "address book"])
        wrapper._add_category(["coding", "open source"])
        self.assertListEqual(wrapper.categories,
                             [["coding", "open source"],
                              ["rfc", "address book"]])


class CarddavObjectFormatDateObject(unittest.TestCase):

    def test_format_date_object_will_not_touch_strings(self):
        expected = 'untouched string'
        actual = carddav_object.CarddavObject._format_date_object(expected,
                                                                  False)
        self.assertEqual(actual, expected)

    def test_format_date_object_with_simple_date_object(self):
        d = datetime.datetime(2018, 2, 13)
        actual = carddav_object.CarddavObject._format_date_object(d, False)
        self.assertEqual(actual, '2018-02-13')

    def test_format_date_object_with_simple_datetime_object(self):
        d = datetime.datetime(2018, 2, 13, 0, 38, 31)
        with mock.patch('time.timezone', -7200):
            actual = carddav_object.CarddavObject._format_date_object(d, False)
        self.assertEqual(actual, '2018-02-13T00:38:31+02:00')

    def test_format_date_object_with_date_1900(self):
        d = datetime.datetime(1900, 2, 13)
        actual = carddav_object.CarddavObject._format_date_object(d, False)
        self.assertEqual(actual, '--02-13')
