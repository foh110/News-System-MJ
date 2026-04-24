package com.xwzx.news;

import com.getcapacitor.BridgeActivity;
import android.widget.Toast;
import android.view.KeyEvent;
import android.os.Build;
import android.window.OnBackInvokedCallback;
import android.window.OnBackInvokedDispatcher;

public class MainActivity extends BridgeActivity {
    private long lastBackPressTime = 0;

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            return handleBackPress();
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    public void onBackPressed() {
        handleBackPress();
    }

    @Override
    public void onStart() {
        super.onStart();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                () -> handleBackPress()
            );
        }
    }

    private boolean handleBackPress() {
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastBackPressTime < 2000) {
            finish();
            return true;
        } else {
            lastBackPressTime = currentTime;
            runOnUiThread(() -> Toast.makeText(this, "再按一次退出应用", Toast.LENGTH_SHORT).show());
            return true;
        }
    }
}
