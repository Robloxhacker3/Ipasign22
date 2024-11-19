import os
import shutil
import subprocess
import zipfile

def sign_ipa(ipa_path, p12_path, mobileprovision_path, password, output_path):
    try:
        # Create working directories
        work_dir = "work_dir"
        payload_dir = os.path.join(work_dir, "Payload")
        os.makedirs(payload_dir, exist_ok=True)

        # Unzip IPA
        with zipfile.ZipFile(ipa_path, 'r') as ipa_zip:
            ipa_zip.extractall(work_dir)

        # Check for the app in Payload
        app_dir = None
        for item in os.listdir(payload_dir):
            if item.endswith(".app"):
                app_dir = os.path.join(payload_dir, item)
                break
        if not app_dir:
            raise Exception("No .app file found in the IPA.")

        # Replace embedded.mobileprovision
        provision_dest = os.path.join(app_dir, "embedded.mobileprovision")
        shutil.copy(mobileprovision_path, provision_dest)

        # Extract certificate from the .p12 file
        keychain_path = os.path.join(work_dir, "temp.keychain")
        p12_cert_path = os.path.join(work_dir, "cert.p12")
        shutil.copy(p12_path, p12_cert_path)

        subprocess.run([
            "security", "create-keychain", "-p", "temp_password", keychain_path
        ], check=True)
        subprocess.run([
            "security", "import", p12_cert_path, "-k", keychain_path, "-P", password,
            "-T", "/usr/bin/codesign"
        ], check=True)
        subprocess.run([
            "security", "unlock-keychain", "-p", "temp_password", keychain_path
        ], check=True)

        # Sign the app
        codesign_command = [
            "codesign",
            "-f", "-s", "iPhone Distribution", "--keychain", keychain_path,
            "--entitlements", os.path.join(app_dir, "entitlements.plist"),
            app_dir
        ]
        subprocess.run(codesign_command, check=True)

        # Rezip the signed app into an IPA
        signed_ipa_path = output_path if output_path.endswith(".ipa") else f"{output_path}.ipa"
        with zipfile.ZipFile(signed_ipa_path, 'w', zipfile.ZIP_DEFLATED) as signed_zip:
            for folder_name, subfolders, filenames in os.walk(work_dir):
                for filename in filenames:
                    file_path = os.path.join(folder_name, filename)
                    arcname = os.path.relpath(file_path, work_dir)
                    signed_zip.write(file_path, arcname)

        print(f"Signed IPA created at: {signed_ipa_path}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)


# Usage example:
ipa_file = "path/to/your.ipa"
p12_file = "path/to/your.p12"
mobileprovision_file = "path/to/your.mobileprovision"
password = "your_p12_password"
output_signed_ipa = "path/to/signed.ipa"

sign_ipa(ipa_file, p12_file, mobileprovision_file, password, output_signed_ipa)
