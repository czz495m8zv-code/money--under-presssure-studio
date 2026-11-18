package com.moneyunderpressure.studio

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

object StudioSettings {
    private const val PREFS = "studio_connection"
    private const val KEY_ALIAS = "money_under_pressure_api_key"
    private const val ANDROID_KEYSTORE = "AndroidKeyStore"

    fun baseUrl(context: Context): String =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString("base_url", "") ?: ""

    fun saveBaseUrl(context: Context, value: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString("base_url", value.trim().trimEnd('/')).apply()
    }

    fun hasToken(context: Context): Boolean =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).contains("token_cipher")

    fun saveToken(context: Context, token: String): Boolean = try {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (token.isBlank()) {
            prefs.edit().remove("token_cipher").remove("token_iv").apply()
        } else {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
            val encrypted = cipher.doFinal(token.toByteArray(Charsets.UTF_8))
            prefs.edit()
                .putString("token_iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
                .putString("token_cipher", Base64.encodeToString(encrypted, Base64.NO_WRAP))
                .apply()
        }
        true
    } catch (_: Exception) {
        false
    }

    fun token(context: Context): String? {
        return try {
            val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            val iv = prefs.getString("token_iv", null) ?: return null
            val encrypted = prefs.getString("token_cipher", null) ?: return null
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(
                Cipher.DECRYPT_MODE, getOrCreateKey(),
                GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP))
            )
            String(cipher.doFinal(Base64.decode(encrypted, Base64.NO_WRAP)), Charsets.UTF_8)
        } catch (_: Exception) {
            null
        }
    }

    private fun getOrCreateKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        val existing = keyStore.getKey(KEY_ALIAS, null) as? SecretKey
        if (existing != null) return existing
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }
}
