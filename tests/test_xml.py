import unittest
from unittest.mock import patch

import requests.exceptions
from argo_probe_xml.exceptions import XMLParseException, RequestException
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
    def test_parse_if_missing_element(self, mock_get):
        mock_get.return_value = xml1
        with self.assertRaises(XMLParseException) as context:
            self.xml1.parse("/aris/partition/nonexisting")

        self.assertEqual(
            context.exception.__str__(),
            "Unable to find element with XPath /aris/partition/nonexisting"
        )

    @patch("argo_probe_xml.xml.XML._get")
    def test_parse_if_wrong_format(self, mock_get):
        mock_get.return_value = xml3
        xml = XML("https://mock3.url.com")
        with self.assertRaises(XMLParseException) as context:
            xml.parse("bla")

        self.assertEqual(
            context.exception.__str__(),
            "Unable to parse xml: "
            "Premature end of data in tag aris line 1, line 1, column 223 "
            "(<string>, line 1)"
        )

    @patch("requests.get")
    def test_get_data(self, mock_get):
        mock_get.side_effect = mock_response_ok
        data = self.xml1._get()
        self.assertEqual(data, xml1)

    @patch("requests.get")
    def test_get_data_with_exception(self, mock_get):
        mock_get.side_effect = mock_response_500
        self.assertRaises(
            RequestException, self.xml1._get
        )