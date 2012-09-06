# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sergey Prokhorov <me@seriyps.ru>

lxml form data extractor

Usage:

>>> from lxml import etree
>>> from urllib import urlencode
>>>
>>> tree = etree.HTML(html_string)
>>> form = tree.xpath("//form[@id='my_form']")[0]
>>> ff = FormFiller()
>>> ff.read(form)
>>> form_data = ff.click('my_submit_button')
>>> form_data
{"my_form_field_name": "my_form_field_value",
 # ...
 "my_submit_button": "my_submit_button_value"}
>>> form_data['some_name'] = 'some_value'
>>> urlencode(form_data)

>>> ff.fill('my_submit_button', some_name1="some_value1",
            some_name2="some_value2")
{...}
>>> ff.fill('my_submit_button', some_not_present_in_form_name=my_value)
KeyError()
"""
import urlparse


class _NodeInterface(object):
    """If you don't use lxml, you need to implement this interface for
    `form` parameter"""

    def __init__(self, tag, attrib=None):
        self.tag = tag
        self.attrib = attrib if self.__is_valid_attrib(attrib) else {}
        self.text = None

    def __is_valid_attrib(self, attrib):
        if (hasattr(attrib, '__getitem__') and hasattr(attrib, 'iteritems')
            and hasattr(attrib, 'get')):
            return True
        return False

    def xpath(self, xpath_expr):
        """@returns: list of 0 or more _NodeInterface()"""
        raise NotImplementedError()


class FormFiller(object):

    def __init__(self, form=None):
        if form:
            self.read(form)

    def _handle_input_text(self, field):
        """text, hidden, password возвращают всегда"""
        return field.attrib.get("value", "")

    _handle_input_hidden = _handle_input_text
    _handle_input_password = _handle_input_text

    def _handle_input_radio(self, field):
        """Radio и checkbox возвращает только если checked"""
        if field.attrib.get("checked", None):
            return field.attrib.get("value")
        else:
            return None

    _handle_input_checkbox = _handle_input_radio

    def _handle_input_submit(self, field):
        """Submit не возвращает если не нажат"""
        self.buttons[field.attrib['name']] = field.attrib.get("value", "")
        return None

    _handle_input_image = _handle_input_button = _handle_input_submit

    def _handle_input(self, field):
        """Для input отдельно отрабатываем каждый type"""
        input_type = field.attrib.get("type", "text")
        return getattr(self, "_handle_input_%s" % input_type)(field)

    def _handle_select(self, field):
        selected = field.xpath("option[@selected]")
        if not selected:
            selected = field[0]
        else:
            selected = selected[0]
        return selected.attrib["value"]

    def _handle_textarea(self, field):
        return field.text

    def read(self, form):
        self.form = form
        self.form_data = {}
        self.buttons = {}
        self.all_fields = set()
        for field in form.xpath(
            "descendant::input|descendant::select|descendant::textarea"):
            if "name" not in field.attrib:
                continue
            name = field.attrib["name"]
            self.all_fields.add(name)
            field_value = getattr(self, "_handle_%s" % field.tag)(field)
            if field_value is None:
                continue
            self.form_data[name] = field_value
        return self.form_data

    def fill(self, button_name, **kwargs):
        assert button_name in self.buttons
        form_params = self.form_data.copy()
        form_params[button_name] = self.buttons[button_name]
        for key, value in kwargs:
            if key not in self.all_fields:
                raise KeyError("Invalid form field name {0}".format(key))
        form_params.update(kwargs)
        return form_params

    def click(self, button_name):
        return self.fill(button_name)

    def _abs_url(self, url, base_url):
        if url.startswith("http://") or url.startswith("https://"):
            # http://example.com/anything ->
            #     http://example.com/anything
            return url
        elif url.startswith("/"):
            # /anything + http://example.com/something ->
            #     http://example.com/anything
            parsed = urlparse.urlsplit(base_url)
            url_parts = (parsed.scheme, parsed.netloc, url, '', '')
        else:
            # anything + http://example.com/dir1/path1 ->
            #     http://example.com/dir1/anything
            parsed = urlparse.urlsplit(base_url)
            base_path = parsed.path.rsplit('/', 1)[0]
            path = base_path + "/" + url
            url_parts = (parsed.scheme, parsed.netloc, path, '', '')
        return urlparse.urlunsplit(url_parts)

    def get_action_url(self, form_page_url):
        if 'action' not in self.form.attrib:
            return form_page_url
        action = self.form.attrib['action']
        return self._abs_url(action, form_page_url)

    def get_method(self):
        return self.form.attrib.get('method', 'GET')
