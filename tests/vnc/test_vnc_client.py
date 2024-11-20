"""Unit tests for WSVNCClient class."""

import asyncio
from unittest import TestCase, mock

import pytest

from wsvnc.rfb.rfb_client import RFBClient
from wsvnc.vnc.vnc_client import WSVNCClient


class TestVNCClient(TestCase):
    def setUp(self):
        self.ticket_url = 'ws://localhost:5800'
    
    @mock.patch('wsvnc.vnc.vnc_client.WSVNCClient._run')
    @mock.patch('threading.Event.wait')
    def fake_init(self, patch_run, patch_wait) -> WSVNCClient:
        """Init client for other tests."""
        vnc = WSVNCClient(self.ticket_url)    
        return vnc
    
    @mock.patch('wsvnc.vnc.vnc_client.WSVNCClient._run')
    @mock.patch('threading.Event.wait')
    def test_init(self, patch_run, patch_wait):
        """Test _init()."""
        vnc = WSVNCClient(self.ticket_url)
        
        patch_run.assert_called_once()
        patch_wait.assert_called_once()
        assert vnc._loop is not None
        assert vnc.ticket_url == self.ticket_url
    
    @mock.patch('wsvnc.vnc.vnc_client.WSVNCClient._run')
    @mock.patch('threading.Event.wait')
    @mock.patch('wsvnc.vnc.vnc_client.WSVNCClient.set_resend_flag')
    def test_init_resend_flag(self, patch_run, patch_wait, patch_set_resend_flag):
        """Test _init() with resend_flag = True."""
        WSVNCClient(self.ticket_url)
        
        patch_set_resend_flag.assert_called_once()
        
    
    @mock.patch('wsvnc.vnc.vnc_client.WSVNCClient._main_loop')
    def test__run(self, main_loop_patch):
        """Test _run()."""
        vnc = self.fake_init()

        vnc._run()
        
        main_loop_patch.assert_called_once()
        
        
    def test_get_screen(self):
        """Verify get_screen() returns not None when screen is not None."""
        vnc = self.fake_init()
        vnc._rfb_client = mock.Mock(spec=RFBClient)
        vnc._rfb_client.img = mock.Mock()
        
        assert vnc.get_screen() is not None
    
    def test_get_screen_bytes(self):
        """Verify get_screen_bytes() returns bytes when screen is not None."""
        vnc = self.fake_init()
        vnc._rfb_client = mock.Mock(spec=RFBClient)
        vnc._rfb_client.img = mock.Mock()
        
        assert isinstance(vnc.get_screen_bytes(), bytes)
    
    def test_get_screen_img_is_none(self):
        """Verify we don't error if the image is none."""
        vnc = self.fake_init()
        vnc._rfb_client = mock.Mock(spec=RFBClient)
        vnc._rfb_client.img = None
        
        assert vnc.get_screen_bytes() is None

    @mock.patch("wsvnc.vnc.vnc_client.WSVNCClient.update_screen")
    def test_set_resend_flag(self, patched_update_screen):
        """Verify the reset flag is set to True."""
        vnc = self.fake_init()
        vnc._rfb_client = mock.Mock(spec=RFBClient)
        vnc._rfb_client.resend_flag = False
        
        vnc.set_resend_flag()
        
        assert vnc._rfb_client.resend_flag
    
    @mock.patch("wsvnc.vnc.vnc_client.WSVNCClient.key_event")
    def test_send_key(self, patched_key_event):
        """Verify we press & release a key."""
        vnc = self.fake_init()
        vnc.send_key(50)
        assert patched_key_event.call_count == 2
    
    @mock.patch("wsvnc.vnc.vnc_client.WSVNCClient.pointer_event")
    def test_mouse_movements(self, patched_pointer_event):
        """Tests all of the movements we implemented."""
        vnc = self.fake_init()
        vnc.move(50, 50)
        vnc.release(50, 50)
        vnc.left_click(50, 50)
        vnc.double_left_click(50, 50)
        vnc.press(50, 50)
        vnc.right_click(50, 50)
        vnc.wheel_up(100, 100)
        vnc.wheel_down(300, 300)
        vnc.wheel(150, 150, 50)
        vnc.wheel(150, 50, 50, True)
        vnc.click_and_drag(50, 50, 100, 100)
        
        patched_pointer_event.assert_called()
        assert patched_pointer_event.call_count == 28
    
    @mock.patch("wsvnc.vnc.vnc_client.WSVNCClient.key_event")
    def test_emit_text(self, patched_key_event):
        """Test emit_text()."""
        vnc = self.fake_init()
        vnc.emit_text("hE1!o")
        
        assert patched_key_event.call_count == 14
        
    def test_main_loop_fail(self):
        """Test that we get an exception when we try a bad conn."""
        with pytest.raises(Exception):
            vnc = self.fake_init()
            vnc.ticket_url = "bad uri"
            
            asyncio.run(vnc._main_loop)
            
        