import datetime
import unittest
from unittest.mock import patch, call

import requests.exceptions
from argo_probe_xml.exceptions import WarningException, CriticalException
from argo_probe_xml.xml import XML

xml1 = b"<aris>" \
         b"<lastUpdate>1659507301</lastUpdate>" \
         b"<partition>" \
         b"<running_jobs>59</running_jobs>" \
         b"<queued_jobs>122</queued_jobs>" \
         b"<allocated_cpus>4640</allocated_cpus>" \
         b"<allocated_nodes>232</allocated_nodes>" \
         b"<free_cpus>3580</free_cpus>" \
         b"<free_nodes>179</free_nodes>" \
         b"<total_nodes>411</total_nodes>" \
         b"<total_cpus>8220</total_cpus>" \
         b"<name>compute</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>" \
         b"<partition>" \
         b"<running_jobs>4</running_jobs>" \
         b"<queued_jobs>0</queued_jobs>" \
         b"<allocated_cpus>13</allocated_cpus>" \
         b"<allocated_nodes>3</allocated_nodes>" \
         b"<free_cpus>867</free_cpus>" \
         b"<free_nodes>41</free_nodes>" \
         b"<total_nodes>44</total_nodes>" \
         b"<total_cpus>880</total_cpus>" \
         b"<name>gpu</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>" \
         b"<partition>" \
         b"<running_jobs>5</running_jobs>" \
         b"<queued_jobs>1</queued_jobs>" \
         b"<allocated_cpus>784</allocated_cpus>" \
         b"<allocated_nodes>20</allocated_nodes>" \
         b"<free_cpus>336</free_cpus>" \
         b"<free_nodes>10</free_nodes>" \
         b"<total_nodes>30</total_nodes>" \
         b"<total_cpus>1120</total_cpus>" \
         b"<name>fat</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>" \
         b"<partition>" \
         b"<running_jobs>1</running_jobs>" \
         b"<queued_jobs>0</queued_jobs>" \
         b"<allocated_cpus>4</allocated_cpus>" \
         b"<allocated_nodes>1</allocated_nodes>" \
         b"<free_cpus>1196</free_cpus>" \
         b"<free_nodes>9</free_nodes>" \
         b"<total_nodes>10</total_nodes>" \
         b"<total_cpus>1200</total_cpus>" \
         b"<name>taskp</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>" \
         b"<partition>" \
         b"<running_jobs>0</running_jobs>" \
         b"<queued_jobs>0</queued_jobs>" \
         b"<allocated_cpus>0</allocated_cpus>" \
         b"<allocated_nodes>0</allocated_nodes>" \
         b"<free_cpus>40</free_cpus>" \
         b"<free_nodes>2</free_nodes>" \
         b"<total_nodes>2</total_nodes>" \
         b"<total_cpus>40</total_cpus>" \
         b"<name>viz</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>" \
         b"<partition>" \
         b"<running_jobs>0</running_jobs>" \
         b"<queued_jobs>0</queued_jobs>" \
         b"<allocated_cpus>0</allocated_cpus>" \
         b"<allocated_nodes>0</allocated_nodes>" \
         b"<free_cpus>360</free_cpus>" \
         b"<free_nodes>16</free_nodes>" \
         b"<total_nodes>16</total_nodes>" \
         b"<total_cpus>360</total_cpus>" \
         b"<name>short</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>" \
         b"<partition>" \
         b"<running_jobs>3</running_jobs>" \
         b"<queued_jobs>2</queued_jobs>" \
         b"<allocated_cpus>6</allocated_cpus>" \
         b"<allocated_nodes>1</allocated_nodes>" \
         b"<free_cpus>34</free_cpus>" \
         b"<free_nodes>0</free_nodes>" \
         b"<total_nodes>1</total_nodes>" \
         b"<total_cpus>40</total_cpus>" \
         b"<name>ml</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>" \
         b"</aris>"

xml2 = \
    b'<?xml version="1.0" encoding="UTF-8"?>' \
    b'<OAI-PMH>' \
    b'<responseDate>2002-02-08T12:00:01Z</responseDate>' \
    b'<request verb="Identify">http://memory.loc.gov/cgi-bin/oai</request>' \
    b'<Identify> ' \
    b'<repositoryName>Library of Congress Open Archive Initiative ' \
    b'Repository 1</repositoryName>' \
    b'<baseURL>http://memory.loc.gov/cgi-bin/oai</baseURL>' \
    b'<protocolVersion>2.0</protocolVersion>' \
    b'<adminEmail>somebody@loc.gov</adminEmail>' \
    b'<adminEmail>anybody@loc.gov</adminEmail>' \
    b'<earliestDatestamp>1990-02-01T12:00:00Z</earliestDatestamp>' \
    b'<deletedRecord>transient</deletedRecord>' \
    b'<granularity>YYYY-MM-DDThh:mm:ssZ</granularity>' \
    b'<compression>deflate</compression>' \
    b'</Identify>' \
    b'</OAI-PMH>'

xml3 = b"<aris>" \
         b"<lastUpdate>1659507301</lastUpdate>" \
         b"<partition>" \
         b"<running_jobs>59</running_jobs>" \
         b"<queued_jobs>122</queued_jobs>" \
         b"<allocated_cpus>4640</allocated_cpus>" \
         b"<allocated_nodes>232</allocated_nodes>" \
         b"<free_cpus>3580</free_cpus>" \
         b"<free_nodes>179</free_nodes>" \
         b"<total_nodes>411</total_nodes>" \
         b"<total_cpus>8220</total_cpus>" \
         b"<name>compute</name>" \
         b"<state_up>up</state_up>" \
         b"</partition>"


class MockResponse:
    def __init__(self, data, status_code):
        self.content = data
        self.status_code = status_code
        self.reason = "BAD REQUEST"

    def raise_for_status(self):
        if not str(self.status_code).startswith("2"):
            raise requests.exceptions.HTTPError(
                f"{self.status_code} {self.reason}"
            )


def mock_response_ok(*args, **kwargs):
    return MockResponse(xml1, status_code=200)


def mock_response_500(*args, **kwargs):
    return MockResponse(None, status_code=500)


class XMLParseTests(unittest.TestCase):
    def setUp(self):
        self.xml1 = XML("https://mock1.url.com")
        self.xml2 = XML("https://mock2.url.com")

    @patch("argo_probe_xml.xml.XML._get")
    def test_parse(self, mock_get):
        mock_get.side_effect = [xml1, xml2, xml2]
        self.assertEqual(
            self.xml1.parse("/aris/partition/state_up"),
            ["up", "up", "up", "up", "up", "up", "up"]
        )
        self.assertEqual(
            self.xml2.parse("/OAI-PMH/Identify/granularity"),
            "YYYY-MM-DDThh:mm:ssZ"
        )
        self.assertEqual(
            self.xml2.parse("/OAI-PMH/Identify/adminEmail"),
            ["somebody@loc.gov", "anybody@loc.gov"]
        )

    @patch("argo_probe_xml.xml.XML._get")
    def test_parse_without_xpath(self, mock_get):
        mock_get.side_effect = [xml1, xml2]
        self.assertTrue(self.xml1.parse())
        self.assertTrue(self.xml2.parse())

    @patch("argo_probe_xml.xml.XML._get")
    def test_parse_if_missing_element(self, mock_get):
        mock_get.return_value = xml1
        with self.assertRaises(CriticalException) as context:
            self.xml1.parse("/aris/partition/nonexisting")

        self.assertEqual(
            context.exception.__str__(),
            "Unable to find element with XPath /aris/partition/nonexisting"
        )

    @patch("argo_probe_xml.xml.XML._get")
    def test_parse_if_wrong_format(self, mock_get):
        mock_get.return_value = xml3
        xml = XML("https://mock3.url.com")
        with self.assertRaises(CriticalException) as context:
            xml.parse("bla")

        self.assertIn("Unable to parse xml", context.exception.__str__())

    @patch("argo_probe_xml.xml.XML._get")
    def test_parse_no_xpath_if_wrong_format(self, mock_get):
        mock_get.return_value = xml3
        xml = XML("https://mock3.url.com")
        with self.assertRaises(CriticalException) as context:
            xml.parse()

        self.assertIn("Unable to parse xml: ", context.exception.__str__())

    @patch("requests.get")
    def test_get_data(self, mock_get):
        mock_get.side_effect = mock_response_ok
        data = self.xml1._get()
        self.assertEqual(data, xml1)

    @patch("requests.get")
    def test_get_data_with_exception(self, mock_get):
        mock_get.side_effect = mock_response_500
        self.assertRaises(CriticalException, self.xml1._get)

    @patch("argo_probe_xml.xml.XML.parse")
    def test_equal_ok(self, mock_parse):
        rv1 = ["up", "up", "up", "up"]
        rv2 = "test"
        mock_parse.side_effect = [rv1, rv2]
        self.assertTrue(
            self.xml1.equal(xpath="/aris/partition/state_up", value="up")
        )
        self.assertTrue(self.xml1.equal(xpath="/mock/path", value="test"))
        self.assertEqual(mock_parse.call_count, 2)
        mock_parse.assert_has_calls([
            call(xpath="/aris/partition/state_up"),
            call(xpath="/mock/path"),
        ])

    @patch("argo_probe_xml.xml.XML.parse")
    def test_not_equal(self, mock_parse):
        rv1 = ["up", "up", "up", "up"]
        rv2 = ["up", "down", "up", "up"]
        rv3 = "test"
        mock_parse.side_effect = [rv1, rv2, rv3]

        with self.assertRaises(CriticalException) as context1:
            self.xml1.equal(xpath="/aris/partition/state_up", value="yes")

        with self.assertRaises(WarningException) as context2:
            self.xml1.equal(xpath="/aris/partition/state_down", value="up")

        with self.assertRaises(CriticalException) as context3:
            self.xml1.equal(xpath="/mock/path", value="something")

        self.assertEqual(mock_parse.call_count, 3)
        mock_parse.assert_has_calls([
            call(xpath="/aris/partition/state_up"),
            call(xpath="/aris/partition/state_down"),
            call(xpath="/mock/path")
        ])

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/partition/state_up: None of the nodes' values equal to 'yes'"
        )
        self.assertEqual(
            context2.exception.__str__(),
            "/aris/partition/state_down: Not all nodes' values equal to 'up'"
        )
        self.assertEqual(
            context3.exception.__str__(),
            "/mock/path: Node value not equal to 'something'"
        )

    @patch("argo_probe_xml.xml.XML.parse")
    def test_warning_threshold(self, mock_parse):
        rv1 = [5, 4, 59, 15, 0, 0, 3]
        rv2 = 60
        mock_parse.side_effect = [
            rv1, rv1, rv1, rv1, rv1, rv2, rv2, rv2, rv2, rv2
        ]

        self.assertEqual(
            self.xml1.warning(
                xpath="/aris/partition/running_jobs", threshold="60"
            ), "OK"
        )

        with self.assertRaises(WarningException) as context1:
            self.xml1.warning(
                xpath="/aris/partition/running_jobs", threshold="50"
            )

        with self.assertRaises(WarningException) as context2:
            self.xml1.warning(
                xpath="/aris/partition/running_jobs", threshold="50:"
            )

        self.assertEqual(
            self.xml1.warning(
                xpath="/aris/partition/running_jobs", threshold="0:70"
            ), "OK"
        )

        with self.assertRaises(WarningException) as context3:
            self.xml1.warning(
                xpath="/aris/partition/running_jobs", threshold="@10:50"
            )

        self.assertEqual(
            self.xml1.warning(xpath="/mock/path", threshold="60"), "OK"
        )

        with self.assertRaises(WarningException) as context4:
            self.xml1.warning(xpath="/mock/path", threshold="10:50")

        self.assertEqual(
            self.xml1.warning(xpath="/mock/path", threshold="10:"), "OK"
        )
        self.assertEqual(
            self.xml1.warning(xpath="/mock/path", threshold="@10:50"), "OK"
        )

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/partition/running_jobs: Partition 2 value outside "
            "range [0, 50.0]"
        )

        self.assertEqual(
            context2.exception.__str__(),
            "/aris/partition/running_jobs: Partitions 0, 1, 3, 4, 5, 6 "
            "values outside range [50.0, Inf]"
        )

        self.assertEqual(
            context3.exception.__str__(),
            "/aris/partition/running_jobs: Partition 3 value inside "
            "range [10.0, 50.0]"
        )

        self.assertEqual(
            context4.exception.__str__(),
            "/mock/path: Value outside range [10.0, 50.0]"
        )

    @patch("argo_probe_xml.xml.XML.parse")
    def test_warning_threshold_with_wrong_defined_threshold(self, mock_parse):
        rv1 = [5, 4, 59, 15, 0, 0, 3]
        rv2 = 60
        mock_parse.side_effect = [rv1, rv2]

        with self.assertRaises(CriticalException) as context1:
            self.xml1.warning(
                xpath="/aris/partition/running_jobs", threshold="x50"
            )

        with self.assertRaises(CriticalException) as context2:
            self.xml1.warning(xpath="/mock/path", threshold="5@0:")

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/partition/running_jobs: Invalid format of warning threshold"
        )

        self.assertEqual(
            context2.exception.__str__(),
            "/mock/path: Invalid format of warning threshold"
        )

    @patch("argo_probe_xml.xml.XML.parse")
    def test_warning_threshold_with_nan_values(self, mock_parse):
        rv1 = ["test1", "test2", "test", "test", "test3", "test1", "test2"]
        rv2 = "something"
        mock_parse.side_effect = [rv1, rv2]

        with self.assertRaises(CriticalException) as context1:
            self.xml1.warning(
                xpath="/aris/partition/running_jobs", threshold="50"
            )

        with self.assertRaises(CriticalException) as context2:
            self.xml1.warning(xpath="/mock/path", threshold="50:")

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/partition/running_jobs: Node values are not numbers"
        )

        self.assertEqual(
            context2.exception.__str__(),
            "/mock/path: Node values are not numbers"
        )

    @patch("argo_probe_xml.xml.XML.parse")
    def test_critical_threshold(self, mock_parse):
        rv1 = [5, 4, 59, 15, 0, 0, 3]
        rv2 = 60
        mock_parse.side_effect = [
            rv1, rv1, rv1, rv1, rv1, rv2, rv2, rv2, rv2, rv2
        ]

        self.assertEqual(
            self.xml1.critical(
                xpath="/aris/partition/running_jobs", threshold="60"
            ), "OK"
        )

        with self.assertRaises(CriticalException) as context1:
            self.xml1.critical(
                xpath="/aris/partition/running_jobs", threshold="50"
            )

        with self.assertRaises(CriticalException) as context2:
            self.xml1.critical(
                xpath="/aris/partition/running_jobs", threshold="50:"
            )

        self.assertEqual(
            self.xml1.critical(
                xpath="/aris/partition/running_jobs", threshold="0:70"
            ), "OK"
        )

        with self.assertRaises(CriticalException) as context3:
            self.xml1.critical(
                xpath="/aris/partition/running_jobs", threshold="@10:50"
            )

        self.assertEqual(
            self.xml1.critical(xpath="/mock/path", threshold="60"), "OK"
        )

        with self.assertRaises(CriticalException) as context4:
            self.xml1.critical(xpath="/mock/path", threshold="10:50")

        self.assertEqual(
            self.xml1.critical(xpath="/mock/path", threshold="10:"), "OK"
        )
        self.assertEqual(
            self.xml1.critical(xpath="/mock/path", threshold="@10:50"), "OK"
        )

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/partition/running_jobs: "
            "Partition 2 value outside range [0, 50.0]"
        )

        self.assertEqual(
            context2.exception.__str__(),
            "/aris/partition/running_jobs: Partitions 0, 1, 3, 4, 5, 6 "
            "values outside range [50.0, Inf]"
        )

        self.assertEqual(
            context3.exception.__str__(),
            "/aris/partition/running_jobs: "
            "Partition 3 value inside range [10.0, 50.0]"
        )

        self.assertEqual(
            context4.exception.__str__(),
            "/mock/path: Value outside range [10.0, 50.0]"
        )

    @patch("argo_probe_xml.xml.XML.parse")
    def test_critical_threshold_with_wrong_defined_threshold(self, mock_parse):
        rv1 = [5, 4, 59, 15, 0, 0, 3]
        rv2 = 60
        mock_parse.side_effect = [rv1, rv2]

        with self.assertRaises(CriticalException) as context1:
            self.xml1.critical(
                xpath="/aris/partition/running_jobs", threshold="x50"
            )

        with self.assertRaises(CriticalException) as context2:
            self.xml1.critical(xpath="/mock/path", threshold="5@0:")

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/partition/running_jobs: Invalid format of critical threshold"
        )

        self.assertEqual(
            context2.exception.__str__(),
            "/mock/path: Invalid format of critical threshold"
        )

    @patch("argo_probe_xml.xml.XML.parse")
    def test_critical_threshold_with_nan_values(self, mock_parse):
        rv1 = ["test1", "test2", "test", "test", "test3", "test1", "test2"]
        rv2 = "something"
        mock_parse.side_effect = [rv1, rv2]

        with self.assertRaises(CriticalException) as context1:
            self.xml1.critical(
                xpath="/aris/partition/running_jobs", threshold="50"
            )

        with self.assertRaises(CriticalException) as context2:
            self.xml1.critical(xpath="/mock/path", threshold="50:")

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/partition/running_jobs: Node values are not numbers"
        )

        self.assertEqual(
            context2.exception.__str__(),
            "/mock/path: Node values are not numbers"
        )

    @patch("argo_probe_xml.xml.get_date_now")
    @patch("argo_probe_xml.xml.XML.parse")
    def test_check_age_ok(self, mock_parse, mock_datetime):
        rv1 = ["1660199401", "1660198775"]
        rv2 = "2022-08-11 08:19:34"
        mock_parse.side_effect = [rv1, rv2]
        mock_datetime.return_value = datetime.datetime(2022, 8, 11, 9, 0, 0)
        self.assertTrue(
            self.xml1.check_if_younger(
                xpath="/aris/lastUpdate", age=3, time_format="UNIX"
            )
        )
        self.assertTrue(
            self.xml1.check_if_younger(
                xpath="/mock/path", age=1, time_format="%Y-%m-%d %H:%M:%S"
            )
        )
        self.assertEqual(mock_parse.call_count, 2)
        mock_parse.assert_has_calls([
            call(xpath="/aris/lastUpdate"), call(xpath="/mock/path")
        ], any_order=True)

    @patch("argo_probe_xml.xml.get_date_now")
    @patch("argo_probe_xml.xml.XML.parse")
    def test_check_age_older(self, mock_parse, mock_datetime):
        rv1 = ["1660199401", "1660198775"]
        rv2 = "2022-08-11 08:19:34"
        mock_parse.side_effect = [rv1, rv1, rv2]
        mock_datetime.return_value = datetime.datetime(2022, 8, 12, 9, 30, 0)
        with self.assertRaises(WarningException) as context1:
            self.xml1.check_if_younger(
                xpath="/aris/lastUpdate", age=3, time_format="UNIX"
            )

        with self.assertRaises(CriticalException) as context2:
            self.xml1.check_if_younger(
                xpath="/aris/lastUpdate", age=2, time_format="UNIX"
            )

        with self.assertRaises(CriticalException) as context3:
            self.xml1.check_if_younger(
                xpath="/mock/path", age=1, time_format="%Y-%m-%d %H:%M:%S"
            )

        self.assertEqual(mock_parse.call_count, 3)
        mock_parse.assert_has_calls([
            call(xpath="/aris/lastUpdate"), call(xpath="/mock/path")
        ], any_order=True)

        self.assertEqual(
            context1.exception.__str__(),
            "/aris/lastUpdate: Some node(s) values are older than 3 hr"
        )
        self.assertEqual(
            context2.exception.__str__(),
            "/aris/lastUpdate: All node(s) values are older than 2 hr"
        )
        self.assertEqual(
            context3.exception.__str__(), "/mock/path: Value older than 1 hr"
        )
