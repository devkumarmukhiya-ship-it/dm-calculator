package com.devkumar.calculator;

import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import com.getcapacitor.BridgeActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

public class MainActivity extends BridgeActivity {

  private WebView printView;
  private volatile boolean jsCanGoBack = false;

  // Back button: if the page is on Settings / History / Loan etc. let the page go back one step; otherwise exit as usual.
  @Override
  @SuppressWarnings("deprecation")
  public void onBackPressed() {
    if (jsCanGoBack) {
      runOnUiThread(new Runnable() {
        @Override
        public void run() {
          getBridge().getWebView().evaluateJavascript("window.dmBack && window.dmBack()", null);
        }
      });
    } else {
      super.onBackPressed();
    }
  }

  @Override
  public void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    getBridge().getWebView().addJavascriptInterface(new NativeHelper(), "AndroidPrint");
  }

  private class NativeHelper {

    @JavascriptInterface
    public void setCanGoBack(boolean value) {
      jsCanGoBack = value;
    }

    // Opens the Android print dialog (printer or "Save as PDF") for the given HTML.
    @JavascriptInterface
    public void print(final String html) {
      runOnUiThread(new Runnable() {
        @Override
        public void run() {
          printView = new WebView(MainActivity.this);
          printView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
              PrintManager pm = (PrintManager) getSystemService(Context.PRINT_SERVICE);
              PrintDocumentAdapter adapter = view.createPrintDocumentAdapter("Repayment Schedule");
              pm.print("Repayment Schedule", adapter, null);
            }
          });
          printView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null);
        }
      });
    }

    // Saves a base64 PDF into the public Downloads folder. Returns "ok" or "error: ...".
    @JavascriptInterface
    public String savePdf(String base64Data, String fileName) {
      try {
        byte[] data = Base64.decode(base64Data, Base64.DEFAULT);
        OutputStream os;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
          ContentValues values = new ContentValues();
          values.put(MediaStore.MediaColumns.DISPLAY_NAME, fileName);
          values.put(MediaStore.MediaColumns.MIME_TYPE, "application/pdf");
          values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
          Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
          if (uri == null) return "error: could not create file";
          os = getContentResolver().openOutputStream(uri);
        } else {
          File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
          dir.mkdirs();
          os = new FileOutputStream(new File(dir, fileName));
        }
        if (os == null) return "error: could not open file";
        os.write(data);
        os.close();
        return "ok";
      } catch (Exception e) {
        return "error: " + e.getMessage();
      }
    }
  }
}
