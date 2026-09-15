// Copyright 2026 Zaid Chromium Extensions Authors
// Use of this source code is governed by a BSD-style license.

#include "chrome/browser/ui/webui/extensions/zaid_crx_install_handler.h"

#include <memory>
#include <utility>

#include "base/check.h"
#include "base/check_op.h"
#include "base/files/file_path.h"
#include "base/functional/bind.h"
#include "base/strings/utf_string_conversions.h"
#include "base/values.h"
#include "chrome/browser/extensions/extension_install_prompt.h"
#include "chrome/browser/extensions/extension_management.h"
#include "chrome/browser/profiles/profile.h"
#include "chrome/browser/ui/select_file_policy/chrome_select_file_policy.h"
#include "chrome/common/pref_names.h"
#include "components/prefs/pref_service.h"
#include "content/public/browser/render_frame_host.h"
#include "content/public/browser/web_contents.h"
#include "content/public/browser/web_ui.h"
#include "extensions/browser/crx_installer.h"
#include "extensions/browser/install_prompt_data.h"
#include "ui/shell_dialogs/selected_file_info.h"

ZaidCrxInstallHandler::ZaidCrxInstallHandler() = default;

ZaidCrxInstallHandler::~ZaidCrxInstallHandler() {
  CloseFileDialog();
}

void ZaidCrxInstallHandler::RegisterMessages() {
  web_ui()->RegisterMessageCallback(
      "zaidInstallCrx",
      base::BindRepeating(&ZaidCrxInstallHandler::HandleInstallCrx,
                          base::Unretained(this)));
}

void ZaidCrxInstallHandler::OnJavascriptDisallowed() {
  weak_factory_.InvalidateWeakPtrs();
  CloseFileDialog();
  callback_id_.clear();
}

void ZaidCrxInstallHandler::CloseFileDialog() {
  if (select_file_dialog_) {
    select_file_dialog_->ListenerDestroyed();
    select_file_dialog_.reset();
  }
}

bool ZaidCrxInstallHandler::CanInstall() {
  Profile* profile = Profile::FromWebUI(web_ui());
  return !profile->IsOffTheRecord() && !profile->IsGuestSession() &&
         !profile->IsChild() &&
         profile->GetPrefs()->GetBoolean(prefs::kExtensionsUIDeveloperMode) &&
         !extensions::ExtensionManagementFactory::GetForBrowserContext(profile)
              ->BlocklistedByDefault();
}

void ZaidCrxInstallHandler::HandleInstallCrx(const base::ListValue& args) {
  CHECK_EQ(args.size(), 1u);
  CHECK(args[0].is_string());
  AllowJavascript();
  const std::string& callback = args[0].GetString();
  if (!callback_id_.empty()) {
    RejectJavascriptCallback(base::Value(callback),
                             base::Value("Ya hay una instalación en curso."));
    return;
  }
  callback_id_ = callback;
  if (!CanInstall()) {
    Finish(false, "Activa el modo desarrollador. La instalación debe estar "
                  "permitida por el perfil y sus políticas.");
    return;
  }
  auto* contents = web_ui()->GetWebContents();
  if (!contents->GetPrimaryMainFrame()->HasTransientUserActivation()) {
    Finish(false, "Pulsa el botón Instalar CRX para seleccionar un archivo.");
    return;
  }
  select_file_dialog_ = ui::SelectFileDialog::Create(
      this, std::make_unique<ChromeSelectFilePolicy>(contents));
  ui::SelectFileDialog::FileTypeInfo types;
  types.extensions = {{FILE_PATH_LITERAL("crx")}};
  types.include_all_files = false;
  select_file_dialog_->SelectFile(
      ui::SelectFileDialog::SELECT_OPEN_FILE, u"Instalar extensión CRX",
      base::FilePath(), &types, 1, FILE_PATH_LITERAL("crx"),
      contents->GetTopLevelNativeWindow());
}

void ZaidCrxInstallHandler::FileSelected(const ui::SelectedFileInfo& file,
                                       int index) {
  CloseFileDialog();
  if (!CanInstall()) {
    Finish(false, "La instalación ya no está permitida.");
    return;
  }
  auto prompt = std::make_unique<ExtensionInstallPrompt>(
      web_ui()->GetWebContents(),
      std::make_unique<extensions::InstallPromptData>(
          extensions::InstallPromptData::UNSET_PROMPT_TYPE));
  auto installer = extensions::CrxInstaller::Create(
      Profile::FromWebUI(web_ui()), std::move(prompt));
  installer->set_error_on_unsupported_requirements(true);
  installer->set_off_store_install_allow_reason(
      extensions::CrxInstaller::OffStoreInstallAllowedFromSettingsPage);
  installer->set_install_immediately(true);
  installer->set_delete_source(false);
  installer->AddInstallerCallback(base::BindOnce(
      &ZaidCrxInstallHandler::OnInstallFinished, weak_factory_.GetWeakPtr()));
  installer->InstallCrx(file.path());
}

void ZaidCrxInstallHandler::FileSelectionCanceled() {
  CloseFileDialog();
  Finish(false);
}

void ZaidCrxInstallHandler::OnInstallFinished(
    const std::optional<extensions::CrxInstallError>& error) {
  Finish(!error.has_value(), error ? base::UTF16ToUTF8(error->message()) : "");
}

void ZaidCrxInstallHandler::Finish(bool installed, const std::string& error) {
  if (callback_id_.empty() || !IsJavascriptAllowed()) {
    return;
  }
  base::Value callback(std::exchange(callback_id_, {}));
  if (error.empty()) {
    ResolveJavascriptCallback(callback, base::Value(installed));
  } else {
    RejectJavascriptCallback(callback, base::Value(error));
  }
}
