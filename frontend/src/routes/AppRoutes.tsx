import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout";
import AssetCategoryPage from "../pages/AssetCategoryPage";
import AssetDetailPage from "../pages/AssetDetailPage";
import AssetFormPage from "../pages/AssetFormPage";
import AssetListPage from "../pages/AssetListPage";
import AssetQrRedirectPage from "../pages/AssetQrRedirectPage";
import CalibrationPage from "../pages/CalibrationPage";
import DashboardPage from "../pages/DashboardPage";
import FoundationPage from "../pages/FoundationPage";
import HierarchyManagementPage from "../pages/HierarchyManagementPage";
import LoginPage from "../pages/LoginPage";
import MaintenancePage from "../pages/MaintenancePage";
import UserManagementPage from "../pages/UserManagementPage";
import TransferPage from "../pages/TransferPage";
import { ProtectedRoute, PublicOnlyRoute, RoleGuard } from "./ProtectedRoute";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      <Route path="/foundation" element={<AppLayout />}>
        <Route index element={<FoundationPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/assets" element={<AssetListPage />} />
          <Route path="/assets/scan" element={<AssetQrRedirectPage />} />
          <Route path="/assets/:assetId" element={<AssetDetailPage />} />
          <Route path="/maintenance" element={<MaintenancePage />} />
          <Route path="/calibrations" element={<CalibrationPage />} />
          <Route
            element={
              <RoleGuard roles={["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"]} />
            }
          >
            <Route path="/transfers" element={<TransferPage />} />
          </Route>
          <Route
            element={<RoleGuard roles={["ULMD_ADMIN", "LAB_MANAGER"]} />}
          >
            <Route path="/assets/register" element={<AssetFormPage />} />
            <Route path="/assets/:assetId/edit" element={<AssetFormPage />} />
          </Route>
          <Route element={<RoleGuard roles={["ULMD_ADMIN"]} />}>
            <Route path="/admin/users" element={<UserManagementPage />} />
            <Route
              path="/admin/hierarchy"
              element={<HierarchyManagementPage />}
            />
            <Route
              path="/admin/asset-categories"
              element={<AssetCategoryPage />}
            />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
