// Copyright 2026 Zaid Chromium Extensions Authors
// Use of this source code is governed by a BSD-style license.

#ifndef CHROME_BROWSER_UI_WEBUI_EXTENSIONS_ZAID_CRX_INSTALL_HANDLER_H_
#define CHROME_BROWSER_UI_WEBUI_EXTENSIONS_ZAID_CRX_INSTALL_HANDLER_H_

#include <optional>
#include <string>

#include "base/memory/scoped_refptr.h"
#include "base/memory/weak_ptr.h"
#include "content/public/browser/web_ui_message_handler.h"
#include "extensions/browser/install/crx_install_error.h"
#include "ui/shell_dialogs/select_file_dialog.h"

class ZaidCrxInstallHandler : public content::WebUIMessageHandler,
                              public ui::SelectFileDialog::Listener {
 public:
  ZaidCrxInstallHandler();
  ~ZaidCrxInstallHandler() override;

  void RegisterMessages() override;
  void OnJavascriptDisallowed() override;
  void FileSelected(const ui::SelectedFileInfo& file, int index) override;
  void FileSelectionCanceled() override;

 private:
  void HandleInstallCrx(const base::ListValue& args);
  void OnInstallFinished(const std::optional<extensions::CrxInstallError>& error);
  void Finish(bool installed, const std::string& error = {});
  void CloseFileDialog();
  bool CanInstall();

  std::string callback_id_;
  scoped_refptr<ui::SelectFileDialog> select_file_dialog_;
  base::WeakPtrFactory<ZaidCrxInstallHandler> weak_factory_{this};
};

#endif  // CHROME_BROWSER_UI_WEBUI_EXTENSIONS_ZAID_CRX_INSTALL_HANDLER_H_
