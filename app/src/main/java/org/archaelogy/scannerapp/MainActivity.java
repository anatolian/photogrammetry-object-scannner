package org.archaelogy.scannerapp;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

public class MainActivity extends Activity {

    TextView response;
    EditText editTextAddress, editTextPort;
    Button buttonConnect;

    int resultCode;
    int request_Code = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        editTextAddress = (EditText) findViewById(R.id.addressEditText);
        editTextPort = (EditText) findViewById(R.id.portEditText);
        buttonConnect = (Button) findViewById(R.id.connectButton);

        response = (TextView) findViewById(R.id.responseTextView);

        SharedPreferences settings = getSharedPreferences("ScannerAppSettings", 0);
        String addr = settings.getString("addr", "");
        String port = settings.getString("port", "");
        editTextAddress.setText(addr);
        editTextPort.setText(port);

        buttonConnect.setOnClickListener(new OnClickListener() {

            @Override
            public void onClick(View arg0) {

                SharedPreferences settings = getApplicationContext().getSharedPreferences("ScannerAppSettings", 0);
                SharedPreferences.Editor editor = settings.edit();
                editor.putString("addr", editTextAddress.getText().toString());
                editor.putString("port", editTextPort.getText().toString());
                editor.commit();

                Intent myIntent = new Intent(MainActivity.this, ScannerInfo.class);
                myIntent.putExtra("addr", editTextAddress.getText().toString()); //Optional parameters
                myIntent.putExtra("port", Integer.parseInt(editTextPort.getText().toString()));
                MainActivity.this.startActivityForResult(myIntent, request_Code);
            }
        });
    }

    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == request_Code) {
            // connect was unsuccessful
            if (resultCode == RESULT_CANCELED) {
                response.setText(data.getData().toString());
            }
            // connect was successful
        }
    }
}
