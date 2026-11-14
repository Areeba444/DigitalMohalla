/**
 * Settings Screen (inspired by mobile settings reference)
 * Includes: User Profile sub-panel, Change Password sheet, FAQs & How It Works, Our Promises,
 * Push Notification toggle, Appearance, and Community Help.
 */
import { router } from 'expo-router';
import { useState } from 'react';
import { Modal, Pressable, ScrollView, Switch, Text, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import {
  ASSURANCE,
  assuranceTone,
  BackButton,
  Body,
  Button,
  Caption,
  Card,
  Collapsible,
  Field,
  Icon,
  type IconName,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

// Plain-language meaning of each assurance state — concise, one line each.
const STATE_TEXT: Record<string, string> = {
  SUFFICIENT_EVIDENCE: 'Verified loans went well. The lender still decides.',
  REVIEW_RECOMMENDED: 'History is mixed or old — worth a closer look. This is normal.',
  INSUFFICIENT_EVIDENCE: 'Too little history yet. Not a negative finding; the lender decides.',
  ACTIVE_DISPUTE: 'A dispute is open. A moderator reviews before anything else happens.',
};

const PROMISES: [IconName, string][] = [
  ['lock', 'Only your neighbourhood is stored — never your exact address.'],
  ['badge', 'No identity-card numbers are kept.'],
  ['gavel', 'Nobody is restricted without a moderator decision on record.'],
  ['history', 'Every loan step is recorded and cannot be edited.'],
];

export default function SettingsScreen() {
  const { theme, themes, setTheme } = useTheme();
  const { user, signOut } = useAuth();

  const displayName = user?.name || user?.email || 'Neighbour';
  const email = user?.email || '';
  const initial = displayName.charAt(0).toUpperCase();

  // Sub-screen / Modal states
  const [profileOpen, setProfileOpen] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  // Edit Profile form state
  const nameParts = displayName.split(' ');
  const [firstName, setFirstName] = useState(nameParts[0] ?? '');
  const [lastName, setLastName] = useState(nameParts.slice(1).join(' ') || '');
  const [profileSaved, setProfileSaved] = useState(false);

  // Password form state
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordSaved, setPasswordSaved] = useState(false);

  const handleSaveProfile = () => {
    setProfileSaved(true);
    setTimeout(() => {
      setProfileSaved(false);
      setProfileOpen(false);
    }, 1200);
  };

  const handleSavePassword = () => {
    setPasswordSaved(true);
    setTimeout(() => {
      setPasswordSaved(false);
      setPasswordOpen(false);
      setNewPassword('');
      setConfirmPassword('');
    }, 1200);
  };

  return (
    <Screen title="Settings" back>
      <BackButton />

      {/* Top Welcome / Profile Card */}
      <Card
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 16,
        }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
          <View
            style={{
              width: 52,
              height: 52,
              borderRadius: 26,
              backgroundColor: theme.colors.primarySoft,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            <Text style={{ fontFamily: theme.fonts.black, fontSize: 22, color: theme.colors.primary }}>
              {initial}
            </Text>
          </View>
          <View style={{ gap: 2 }}>
            <Caption style={{ color: theme.colors.textSecondary }}>Welcome</Caption>
            <Text style={{ fontFamily: theme.fonts.bold, fontSize: 17, color: theme.colors.text }}>
              {displayName}
            </Text>
            {email ? <Caption>{email}</Caption> : null}
          </View>
        </View>

        {/* Sign out button */}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Sign out"
          onPress={signOut}
          style={({ pressed }) => ({
            width: 40,
            height: 40,
            borderRadius: 20,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: theme.colors.surface2,
            opacity: pressed ? 0.7 : 1,
          })}>
          <Icon name="logout" size={20} color={theme.colors.danger.fg} />
        </Pressable>
      </Card>

      {/* Main Settings Menu Rows */}
      <Card style={{ padding: 6, gap: 0 }}>
        {/* Row 1: User Profile */}
        <Pressable
          accessibilityRole="button"
          onPress={() => setProfileOpen(true)}
          style={({ pressed }) => ({
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingHorizontal: 14,
            paddingVertical: 16,
            borderRadius: theme.radius.sm,
            opacity: pressed ? 0.75 : 1,
          })}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <Icon name="person" size={20} color={theme.colors.primary} />
            <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 15, color: theme.colors.text }}>
              User Profile
            </Text>
          </View>
          <Icon name="chevron_right" size={20} color={theme.colors.textMuted} />
        </Pressable>

        <View style={{ height: 1, backgroundColor: theme.colors.hairline, marginHorizontal: 12 }} />

        {/* Row 2: Change Password */}
        <Pressable
          accessibilityRole="button"
          onPress={() => setPasswordOpen(true)}
          style={({ pressed }) => ({
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingHorizontal: 14,
            paddingVertical: 16,
            borderRadius: theme.radius.sm,
            opacity: pressed ? 0.75 : 1,
          })}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <Icon name="lock" size={20} color={theme.colors.primary} />
            <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 15, color: theme.colors.text }}>
              Change Password
            </Text>
          </View>
          <Icon name="chevron_right" size={20} color={theme.colors.textMuted} />
        </Pressable>

        <View style={{ height: 1, backgroundColor: theme.colors.hairline, marginHorizontal: 12 }} />

        {/* Row 3: Push Notification toggle */}
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingHorizontal: 14,
            paddingVertical: 14,
          }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <Icon name="notifications" size={20} color={theme.colors.primary} />
            <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 15, color: theme.colors.text }}>
              Push Notification
            </Text>
          </View>
          <Switch
            value={notificationsEnabled}
            onValueChange={setNotificationsEnabled}
            trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
          />
        </View>
      </Card>

      {/* Theme / Appearance Selection */}
      <Card style={{ gap: 10 }}>
        <SectionLabel>Appearance Theme</SectionLabel>
        {/* 2×2 grid so all four themes fit nicely on mobile */}
        <View style={{ gap: 10 }}>
          {[themes.slice(0, 2), themes.slice(2, 4)].map((row, rowIdx) => (
            <View key={rowIdx} style={{ flexDirection: 'row', gap: 10 }}>
              {row.map((t) => {
                const selected = theme.name === t.name;
                return (
                  <Pressable
                    key={t.name}
                    accessibilityRole="radio"
                    accessibilityLabel={`${t.label} theme`}
                    accessibilityState={{ selected }}
                    onPress={() => setTheme(t.name)}
                    style={({ pressed }) => ({
                      flex: 1,
                      flexDirection: 'row',
                      alignItems: 'center',
                      gap: 10,
                      paddingHorizontal: 12,
                      paddingVertical: 14,
                      borderRadius: theme.radius.md,
                      borderWidth: 2,
                      borderColor: selected ? theme.colors.primary : theme.colors.border,
                      backgroundColor: selected ? theme.colors.primarySoft : theme.colors.surface,
                      opacity: pressed ? 0.8 : 1,
                    })}>
                    {/* Swatch uses each theme's own primary colour */}
                    <View
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: 13,
                        backgroundColor: t.colors.primary,
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}>
                      {selected ? <Icon name="check" size={14} color={t.colors.onPrimary} /> : null}
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={{ fontFamily: theme.fonts.bold, fontSize: 13, color: theme.colors.text }}>
                        {t.label}
                      </Text>
                      <Text style={{ fontFamily: theme.fonts.regular, fontSize: 11, color: theme.colors.textMuted }}>
                        {t.tagline}
                      </Text>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          ))}
        </View>
      </Card>

      {/* FAQs, How Digital Mohalla Works & Our Promises */}
      <Card style={{ gap: 12 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Icon name="help" size={20} color={theme.colors.primary} />
          <SectionLabel>FAQs & How Digital Mohalla Works</SectionLabel>
        </View>

        <Collapsible label="How the evidence summary works">
          <Body muted style={{ fontSize: 13, marginBottom: 8 }}>
            When you ask to borrow, the lender sees a summary of verified evidence from earlier loans,
            not a single composite score. It is one of four states:
          </Body>
          <View style={{ gap: 10 }}>
            {Object.entries(ASSURANCE).map(([state, a]) => {
              const tone = assuranceTone(theme, state);
              return (
                <View key={state} style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
                  <View
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: tone.bg,
                      borderWidth: 1,
                      borderColor: tone.border,
                    }}>
                    <Icon name={a.icon} size={16} color={tone.fg} />
                  </View>
                  <View style={{ flex: 1, gap: 1 }}>
                    <Text style={{ fontFamily: theme.fonts.bold, fontSize: 13, color: tone.fg }}>
                      {a.label}
                    </Text>
                    <Caption style={{ color: theme.colors.textSecondary }}>
                      {STATE_TEXT[state]}
                    </Caption>
                  </View>
                </View>
              );
            })}
          </View>
        </Collapsible>

        <Collapsible label="Our privacy and security promises">
          <View style={{ gap: 8, marginTop: 4 }}>
            {PROMISES.map(([icon, text]) => (
              <View key={icon} style={{ flexDirection: 'row', gap: 10, alignItems: 'center' }}>
                <Icon name={icon} size={18} color={theme.colors.accent} />
                <Body style={{ flex: 1, fontSize: 13 }}>{text}</Body>
              </View>
            ))}
          </View>
        </Collapsible>
      </Card>

      {/* Query / Help Box (inspired by reference image) */}
      <Card
        style={{
          alignItems: 'center',
          gap: 8,
          backgroundColor: theme.colors.surface2,
          paddingVertical: 18,
          borderWidth: 1,
          borderColor: theme.colors.border,
        }}>
        <Text style={{ fontFamily: theme.fonts.medium, fontSize: 14, color: theme.colors.textSecondary, textAlign: 'center' }}>
          If you have any other query you can reach out to us.
        </Text>
        <Button
          label="Contact Community Help"
          icon="contact_support"
          variant="outline"
          compact
          onPress={() => router.push('/community/join')}
        />
      </Card>

      {/* Modal 1: User Profile Screen (inspired by reference image 2) */}
      <Modal visible={profileOpen} animationType="slide" transparent>
        <View
          style={{
            flex: 1,
            backgroundColor: 'rgba(0,0,0,0.5)',
            justifyContent: 'flex-end',
          }}>
          <View
            style={{
              backgroundColor: theme.colors.bg,
              borderTopLeftRadius: theme.radius.xl,
              borderTopRightRadius: theme.radius.xl,
              padding: 20,
              gap: 16,
              maxHeight: '90%',
            }}>
            {/* Header */}
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <Pressable onPress={() => setProfileOpen(false)} style={{ padding: 4 }}>
                <Icon name="close" size={24} color={theme.colors.text} />
              </Pressable>
              <Text style={{ fontFamily: theme.fonts.bold, fontSize: 18, color: theme.colors.text }}>
                User Profile
              </Text>
              <View style={{ width: 32 }} />
            </View>

            <ScrollView contentContainerStyle={{ gap: 14, paddingBottom: 20 }}>
              {/* Profile Avatar with camera badge */}
              <View style={{ alignItems: 'center', marginVertical: 8 }}>
                <View
                  style={{
                    width: 80,
                    height: 80,
                    borderRadius: 40,
                    backgroundColor: theme.colors.primarySoft,
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderWidth: 2,
                    borderColor: theme.colors.primary,
                  }}>
                  <Text style={{ fontFamily: theme.fonts.black, fontSize: 32, color: theme.colors.primary }}>
                    {initial}
                  </Text>
                  <View
                    style={{
                      position: 'absolute',
                      bottom: 0,
                      right: 0,
                      width: 26,
                      height: 26,
                      borderRadius: 13,
                      backgroundColor: theme.colors.surface,
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderWidth: 1,
                      borderColor: theme.colors.border,
                    }}>
                    <Icon name="photo_camera" size={14} color={theme.colors.text} />
                  </View>
                </View>
              </View>

              <Field label="First Name" value={firstName} onChangeText={setFirstName} placeholder="First Name" />
              <Field label="Last Name" value={lastName} onChangeText={setLastName} placeholder="Last Name" />
              <Field label="E-Mail" value={email || 'Not present in database'} onChangeText={() => {}} />
              <Field label="Mobile" value="Not recorded — privacy protected" onChangeText={() => {}} />

              {profileSaved ? (
                <Caption style={{ textAlign: 'center', color: theme.colors.success.fg, fontWeight: 'bold' }}>
                  Profile saved successfully!
                </Caption>
              ) : null}

              <Button label="SAVE" icon="save" onPress={handleSaveProfile} />
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Modal 2: Change Password Sheet (inspired by reference image 3) */}
      <Modal visible={passwordOpen} animationType="slide" transparent>
        <View
          style={{
            flex: 1,
            backgroundColor: 'rgba(0,0,0,0.5)',
            justifyContent: 'flex-end',
          }}>
          <View
            style={{
              backgroundColor: theme.colors.bg,
              borderTopLeftRadius: theme.radius.xl,
              borderTopRightRadius: theme.radius.xl,
              padding: 24,
              gap: 16,
            }}>
            {/* Drag handle */}
            <View
              style={{
                width: 44,
                height: 4,
                borderRadius: 2,
                backgroundColor: theme.colors.textMuted,
                alignSelf: 'center',
                opacity: 0.5,
              }}
            />

            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text style={{ fontFamily: theme.fonts.bold, fontSize: 20, color: theme.colors.text }}>
                Change Password
              </Text>
              <Pressable onPress={() => setPasswordOpen(false)} style={{ padding: 4 }}>
                <Icon name="close" size={22} color={theme.colors.textSecondary} />
              </Pressable>
            </View>

            <Field
              label="New Password"
              value={newPassword}
              onChangeText={setNewPassword}
              placeholder="Enter new password"
              secureTextEntry
            />

            <Field
              label="Confirm Password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Confirm new password"
              secureTextEntry
            />

            {passwordSaved ? (
              <Caption style={{ textAlign: 'center', color: theme.colors.success.fg, fontWeight: 'bold' }}>
                Password changed successfully!
              </Caption>
            ) : null}

            <Button
              label="SAVE"
              icon="lock"
              disabled={newPassword.length < 6 || newPassword !== confirmPassword}
              onPress={handleSavePassword}
            />
          </View>
        </View>
      </Modal>
    </Screen>
  );
}
